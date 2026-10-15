"""Pulls lessons, tasks and grades into data/planner_data.json.
Run: python sync.py [--days-back N --days-ahead N]"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import threading
from functools import wraps
from datetime import date, datetime, timedelta
from pathlib import Path

from smartschool import (
    FutureTasks,
    PlannedElement,
    Smartschool,
    SmartschoolHours,
    SmartschoolLessons,
    SmartschoolMomentInfos,
)

try:
    from smartschool import ApplicableAssignmentTypes
except ImportError:
    ApplicableAssignmentTypes = None

try:
    from smartschool import StudentNotes, StudentNoteDetails, StudentAbsences
except ImportError:  # Older source-run environments must still be able to sync the planner.
    StudentNotes = StudentNoteDetails = StudentAbsences = None

from dutch_dates import resolve_due_date
import gemini_dates
import planner_details
import app_errors
import task_state
import credential_store
from secure_session import SecureSmartschool
from version import __version__

_regex_active = False  # resolved from the saved choice and key at the start of each sync
_run_lock = threading.Lock()


class TimeoutSmartschool(SecureSmartschool):
    def __init__(self, creds):
        super().__init__(creds, ROOT)


def serial_sync(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        with _run_lock:
            if os.name != 'nt':
                return function(*args, **kwargs)
            import ctypes
            from ctypes import wintypes
            api = ctypes.WinDLL('kernel32', use_last_error=True)
            api.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
            api.CreateMutexW.restype = wintypes.HANDLE
            api.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
            api.WaitForSingleObject.restype = wintypes.DWORD
            api.ReleaseMutex.argtypes = [wintypes.HANDLE]
            api.CloseHandle.argtypes = [wintypes.HANDLE]
            name = 'Local\\SmartschoolPlannerSync-' + hashlib.sha256(str(ROOT.resolve()).casefold().encode()).hexdigest()
            handle = api.CreateMutexW(None, False, name)
            if not handle:
                raise OSError('Could not lock planner sync')
            acquired = False
            try:
                acquired = api.WaitForSingleObject(handle, 0xFFFFFFFF) in (0, 0x80)
                if not acquired:
                    raise OSError('Could not lock planner sync')
                return function(*args, **kwargs)
            finally:
                if acquired:
                    api.ReleaseMutex(handle)
                api.CloseHandle(handle)
    return wrapped


def write_snapshot(path: Path, data: dict) -> None:
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as file:
            temporary = Path(file.name)
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def get_root() -> Path:
    """Program folder (the exe's folder when packaged)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


ROOT = get_root()
DATA_DIR = ROOT / "data"
OUTPUT_FILE = DATA_DIR / "planner_data.json"

# status flags meaning "nothing here"; anything else may have info
EMPTY_ISH = {"", "0", "false", "no", "none", None}


def looks_truthy(value) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() not in EMPTY_ISH


def fmt_person(name_obj) -> str:
    """PersonDescription -> display name."""
    if name_obj is None:
        return ""
    return getattr(name_obj, "starting_with_first_name", None) or getattr(name_obj, "starting_with_last_name", "") or ""


def fmt_people(users) -> str:
    return ", ".join(filter(None, (fmt_person(u.name) for u in users)))


def build_hours_lookup(session: Smartschool) -> dict:
    """hour_id -> {start, end, title}"""
    lookup = {}
    for hour in SmartschoolHours(session):
        lookup[hour.hour_id] = {"start": hour.start, "end": hour.end, "title": hour.title}
    return lookup


def parse_structured_deadline(raw: str | None) -> date | None:
    """Structured deadline field (format unconfirmed: empty, ISO or DD/MM/YYYY)."""
    if not raw or not str(raw).strip():
        return None
    raw = str(raw).strip()
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        pass
    m = re.match(r"^(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})$", raw)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if year < 100:
            year += 2000
        try:
            return date(year, month, day)
        except ValueError:
            return None
    return None


def resolve_due_date_sync(explicit_deadline: str | None, free_text: str, reference_date: date) -> tuple[str, bool, str, bool]:
    """Resolve a due date without network: structured deadline, then the regex parser if enabled.
    Returns (due_date_iso, was_corrected, source, needs_ai)."""
    structured = parse_structured_deadline(explicit_deadline)
    if structured:
        return structured.isoformat(), structured != reference_date, "structured", False

    if _regex_active:
        due_date, inferred = resolve_due_date(free_text, reference_date)
        if inferred:
            return due_date.isoformat(), True, "regex", False

    return reference_date.isoformat(), False, "none", True


def _register_for_ai(pending: list[dict], free_text: str, reference_date: date, entries: list[dict]) -> None:
    """Queue dicts to patch together once the AI pass resolves this item."""
    if free_text and free_text.strip():
        pending.append({"text": free_text, "posted": reference_date, "entries": entries})


def stable_task_id(course: str, type_: str, description: str, due_date: str) -> str:
    """Content-hash id that survives re-syncs. Call only once due_date is final (after the AI pass)."""
    raw = f"{course}|{type_}|{description}|{due_date}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def assign_task_ids(todos, days, previous, account):
    """Reuse existing state IDs and keep the mapping after tasks leave the sync window."""
    path = DATA_DIR / 'task_identities.json'
    try:
        registry = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(registry, dict) or not all(isinstance(k, str) and isinstance(v, str) and v for k, v in registry.items()):
            raise ValueError('Invalid task identity registry')
    except FileNotFoundError:
        registry = {}
    except (ValueError, OSError):
        raise ValueError('Saved task identities could not be read. Existing planner data was kept.') from None

    def semantic(task):
        return tuple(str(task.get(k) or '').strip() for k in ('course', 'type', 'description', 'posted_date'))

    def server_id(task):
        server = task.get('source_id')
        if server and str(server).startswith('future:'):
            server = str(server)[7:]
        if not server and task.get('element_source') == 'planner_api':
            server = task.get('moment_id')
        return server

    def identity(task):
        server = server_id(task)
        value = ['server', str(server)] if server else ['content', *semantic(task)]
        return hashlib.sha256(json.dumps([account, value], ensure_ascii=False).encode('utf-8')).hexdigest()

    old, server_owners = {}, {}
    for task in previous.get('todos', []):
        if task.get('id'):
            if not server_id(task):
                old.setdefault(semantic(task), set()).add(task['id'])
            registry.setdefault(identity(task), task['id'])
            if server_id(task):
                server_owners.setdefault(task['id'], set()).add(identity(task))

    identities = {}
    for task in todos:
        identities.setdefault(semantic(task), set()).add(identity(task))
    consumed = {registry[identity(task)] for task in todos if identity(task) in registry}
    claimed = {}
    for task in todos:
        key = identity(task)
        candidates = old.get(semantic(task), set()) - consumed
        if key not in registry:
            registry[key] = next(iter(candidates)) if len(candidates) == 1 and len(identities[semantic(task)]) == 1 else key[:24]
            consumed.add(registry[key])
        candidate = registry[key]
        owners = server_owners.get(candidate, set())
        if len(owners) > 1:
            registry[key] = key  # An already merged state cannot safely be attributed to either task.
        elif (owners and key not in owners) or (candidate in claimed and claimed[candidate] != key):
            registry[key] = key[:24]
        claimed[registry[key]] = key
        task['id'] = registry[key]

    merged, aliases = {}, {}
    for task in todos:
        key = task['id']
        if key in merged:
            aliases[task['id']] = key
            registry[identity(task)] = key
            target = merged[key]
            # Prefer the richer lesson record over the lightweight future-task view.
            if task.get('source') != 'future_tasks':
                target.update({k: v for k, v in task.items() if v not in (None, '', [], {}) and k != 'id'})
            else:
                for field in ('body', 'attachments', 'weblinks', 'detail_fields'):
                    if not target.get(field) and task.get(field):
                        target[field] = task[field]
            target['id'] = key
        else:
            merged[key] = task

    for day in days:
        for event in day['events']:
            for assignment in (event.get('info') or {}).get('assignments', []):
                task = dict(assignment, course=event['course'], posted_date=day['date'],
                            moment_id=event.get('moment_id'), element_source=event.get('source'))
                assignment['id'] = registry[identity(task)]
    task_state.migrate_task_ids(ROOT, aliases)
    write_snapshot(path, registry)
    return sorted(merged.values(), key=lambda task: task['due_date'])


def _flatten_raw(obj, prefix: str = "") -> list[tuple[str, str]]:
    """Flatten nested JSON into (path, value) pairs of non-empty string/number leaves."""
    out: list[tuple[str, str]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.extend(_flatten_raw(v, f"{prefix}.{k}" if prefix else k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.extend(_flatten_raw(v, f"{prefix}[{i}]"))
    elif isinstance(obj, str):
        s = obj.strip()
        if s:
            out.append((prefix, s))
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        out.append((prefix, str(obj)))
    return out


# backend-plumbing field names: hidden from the detail view, still date-scanned
_TECHNICAL_LEAF_NAMES = {
    "id", "platformid", "sort", "color", "resolvedstatus", "unconfirmed",
    "pinned", "isparticipant", "onlinesession", "plannedelementtype",
    "wholeday", "deadline",
}


def _is_technical_field(path: str) -> bool:
    last = path.rsplit(".", 1)[-1].split("[")[0].lower()
    return last in _TECHNICAL_LEAF_NAMES


# Core fetches that failed during this sync (they are best-effort, but if ALL fail the sync must not look successful)
_fetch_errors: dict[str, Exception] = {}
_planner_diagnostics: dict[str, dict] = {}


def parse_planner_records(raw_elements, source: str):
    """Keep valid records and record schema failures without storing student content."""
    if not isinstance(raw_elements, list):
        _planner_diagnostics[source] = {'status': 'invalid_response', 'error': 'ExpectedList'}
        raise ValueError('Planner returned an unexpected response format')
    status = {'status': 'ok', 'received': len(raw_elements), 'parsed': 0, 'skipped': 0, 'schema_errors': []}
    _planner_diagnostics[source] = status
    for raw in raw_elements:
        try:
            element = PlannedElement(**raw)
        except (ValueError, TypeError) as exc:
            status['skipped'] += 1
            status['status'] = 'partial'
            # Pydantic exception strings include input values; store field names and error codes only.
            from pydantic import ValidationError
            if isinstance(exc, ValidationError):
                for error in exc.errors(include_input=False, include_context=False, include_url=False):
                    item = {'field': '.'.join(str(part) for part in error['loc']), 'type': error['type']}
                    if item not in status['schema_errors'] and len(status['schema_errors']) < 12:
                        status['schema_errors'].append(item)
            continue
        status['parsed'] += 1
        yield raw, element
    if raw_elements and not status['parsed']:
        status['status'] = 'failed'
        raise ValueError('All planner records failed validation')


_ISO_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2})?([.,]\d+)?(Z|[+-]\d{2}:?\d{2})?)?$")
_UUID_LIKE_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def build_deadline_text(display_text: str, body_text: str, raw_fields, detail_raw_fields) -> str:
    """Text the deadline detector reads for one task.

    Normally just the title plus "Info voor de leerling" (the student-facing text). Teacher-only
    notes, linked items, ids and timestamps are left out: they only add noise, burn the per-task
    length limit and make every task look date-like. If the body couldn't be fetched, fall back to
    the other text fields, still without ids and timestamps.
    """
    if body_text and body_text.strip():
        return f"{display_text}\n\n{body_text}".strip()
    parts = [display_text]
    for path, value in list(raw_fields) + list(detail_raw_fields):
        v = str(value).strip()
        if not v or _is_technical_field(path) or _ISO_TS_RE.match(v) or _UUID_LIKE_RE.match(v):
            continue
        if path.rsplit(".", 1)[-1].split("[")[0].lower() in ("privateinfo", "linkedplannedelement"):
            continue
        if ".linkedPlannedElement" in path or "privateInfo" in path:
            continue
        if v.lower() in display_text.lower():
            continue  # already included (e.g. the title again)
        parts.append(v)
    return " ".join(parts).strip()


def fetch_moment_info(
    session: Smartschool, moment_id: str, lesson_date: date, course: str, pending: list[dict]
) -> dict | None:
    try:
        info = SmartschoolMomentInfos(session, moment_id)
        # yields one element per xpath match; take the first
        for item in info:
            assignments = []
            for a in item.assignments:
                free_text = " ".join(filter(None, [a.description, a.atdescription, a.assignment_info]))
                due_date, corrected, source, needs_ai = resolve_due_date_sync(a.assignment_deadline, free_text, lesson_date)
                detail_fields = [
                    [label, val]
                    for label, val in [
                        ("type", a.type),
                        ("description", a.description),
                        ("atdescription", a.atdescription),
                        ("assignment_info", a.assignment_info),
                        ("assignment_deadline", a.assignment_deadline),
                        ("materials", item.materials),
                    ]
                    if val
                ]
                assignment = {
                    "id": None,  # set in run()
                    "type": a.type,
                    "description": a.description,
                    "info": a.assignment_info,
                    "body": a.assignment_info or '',
                    "due_date": due_date,
                    "due_date_corrected": corrected,
                    "due_date_source": source,
                    "warning": looks_truthy(a.warning),
                    "detail_fields": detail_fields,
                }
                if needs_ai:
                    _register_for_ai(pending, free_text, lesson_date, [assignment])
                assignments.append(assignment)
            return {
                "class_name": item.class_name,
                "subject": item.subject,
                "materials": item.materials,
                "assignments": assignments,
            }
    except Exception as exc:  # noqa: BLE001 - best effort
        print(f"  (could not fetch moment info for {moment_id}: {exc})", file=sys.stderr)
    return None


def build_lessons_legacy(
    session: Smartschool, start_date: date, cutoff: date, pending: list[dict]
) -> list[dict]:
    """Legacy XML agenda (empty on Smartschool Next schools). Covers ~20 days per call, so call repeatedly and dedupe by moment_id."""
    hours = build_hours_lookup(session)
    by_date: dict[str, list[dict]] = {}
    seen_moment_ids: set[str] = set()

    anchor = start_date
    while anchor <= cutoff:
        for lesson in SmartschoolLessons(session, timestamp_to_use=anchor):
            lesson_date = lesson.date
            if lesson_date < start_date or lesson_date > cutoff:
                continue
            if lesson.moment_id in seen_moment_ids:
                continue
            seen_moment_ids.add(lesson.moment_id)

            hour_info = hours.get(lesson.hour_id, {})
            has_flagged_info = any(
                looks_truthy(v)
                for v in (
                    lesson.assignment_end_status,
                    lesson.test_deadline_status,
                    lesson.note_status,
                    lesson.note,
                )
            )

            entry = {
                "moment_id": lesson.moment_id,
                "start": hour_info.get("start", ""),
                "end": hour_info.get("end", ""),
                "course": lesson.course_title or lesson.course,
                "classroom": lesson.classroom_title or lesson.classroom,
                "teacher": lesson.teacher_title or lesson.teacher,
                "groups": lesson.klassen_title or lesson.klassen,
                "note": lesson.note,
                "title": lesson.subject,  # lesson title/explanation
                "has_info": has_flagged_info,
                "info": None,  # set below if has_flagged_info
                "source": "legacy_agenda",
            }

            if has_flagged_info:
                print(f"  fetching detail for {entry['course']} on {lesson_date} ...")
                entry["info"] = fetch_moment_info(session, lesson.moment_id, lesson_date, entry["course"], pending)

            by_date.setdefault(lesson_date.isoformat(), []).append(entry)

        anchor += timedelta(days=18)  # overlap between windows

    return by_date


def build_lessons_planner_api(
    session: Smartschool,
    start_date: date,
    cutoff: date,
    pending: list[dict],
    detail_fetcher: planner_details.DetailFetcher | None,
) -> dict[str, list[dict]]:
    """Planner cards (assignments, to-dos) from the Smartschool Next REST API.
    The list returns titles only; body text is fetched per item by detail_fetcher."""
    user_id = session.authenticated_user["id"]

    raw_elements = session.json(
        f"/planner/api/v1/planned-elements/user/{user_id}",
        data={"from": start_date.isoformat(), "to": cutoff.isoformat(), "types": "planned-assignments,planned-to-dos"},
    )

    by_date: dict[str, list[dict]] = {}

    for raw, pe in parse_planner_records(raw_elements, 'planner'):
        posted_date = pe.period.date_time_from.date()

        course_names = ", ".join(str(c.name) for c in pe.courses) or None
        location = ", ".join(filter(None, (f"{l.title} {l.number}".strip() for l in pe.locations)))
        teacher = fmt_people(pe.organisers.users) if pe.organisers else ""
        groups = ", ".join(str(g.name) for g in pe.participants.groups) if pe.participants else ""
        title = str(pe.name)
        element_type = str(pe.planned_element_type)

        # body text: see planner_details.py
        detail_payload = None
        if detail_fetcher is not None:
            detail_payload = detail_fetcher.fetch(str(pe.id), element_type, posted_date, title)
        raw = planner_details.public_payload(raw)
        detail_payload = planner_details.public_payload(detail_payload)
        body_text = planner_details.extract_body(detail_payload, title) if detail_payload else ""

        # description stays the title (keeps task ids stable); body is stored separately
        extra_text_parts = []
        for key in ("description", "content", "remark", "comment", "text", "body"):
            val = raw.get(key)
            if isinstance(val, str) and val.strip():
                extra_text_parts.append(val.strip())
        display_text = " ".join([title, *extra_text_parts]).strip()

        # deadline scan text: body plus every other field
        raw_fields = _flatten_raw(raw)
        detail_raw_fields = _flatten_raw(detail_payload) if detail_payload else []
        scan_text = build_deadline_text(display_text, body_text, raw_fields, detail_raw_fields)

        # Smartschool's own deadline wins; else resolve now or queue for the AI pass
        if pe.period.deadline:
            due_date = pe.period.date_time_to.date().isoformat()
            due_corrected = due_date != posted_date.isoformat()
            due_source = "structured"
            needs_ai = False
        else:
            due_date, due_corrected, due_source, needs_ai = resolve_due_date_sync(None, scan_text, posted_date)

        assignment_type = pe.assignment_type.name if pe.assignment_type else element_type
        entry_course = course_names or title
        detail_fields = [[path, val] for path, val in raw_fields if not _is_technical_field(path)]
        detail_fields += [[f"detail.{path}", val] for path, val in detail_raw_fields if not _is_technical_field(path)]

        assignment = {
            "id": None,  # set in run()
            "type": assignment_type,
            "description": display_text,
            "body": body_text,
            "attachments": planner_details.extract_links(detail_payload)["attachments"] if detail_payload else [],
            "weblinks": planner_details.extract_links(detail_payload)["weblinks"] if detail_payload else [],
            "info": None,
            "due_date": due_date,
            "due_date_corrected": due_corrected,
            "due_date_source": due_source,
            "warning": False,
            "detail_fields": detail_fields,
        }
        if needs_ai:
            _register_for_ai(pending, scan_text, posted_date, [assignment])

        entry = {
            "moment_id": str(pe.id),
            "start": pe.period.date_time_from.strftime("%H:%M"),
            "end": pe.period.date_time_to.strftime("%H:%M"),
            "course": entry_course,
            "classroom": location,
            "teacher": teacher,
            "groups": groups,
            "note": None,
            "title": title,
            "has_info": True,
            "element_type": element_type,
            "info": {
                "class_name": course_names,
                "subject": None,
                "materials": None,
                "assignments": [assignment],
            },
            "source": "planner_api",
        }

        by_date.setdefault(posted_date.isoformat(), []).append(entry)

    return by_date


def build_all_classes_planner_api(session: Smartschool, start_date: date, cutoff: date) -> dict[str, list[dict]]:
    """Best-effort fetch of every class period; unsupported records are reported."""
    user_id = session.authenticated_user["id"]
    url = f"/planner/api/v1/planned-elements/user/{user_id}"
    base_data = {"from": start_date.isoformat(), "to": cutoff.isoformat()}

    parsed_elements = []
    empty_response = False
    rejected_records = False
    last_exc: Exception | None = None
    # broadest filter first, then the known-working one
    for types_guess in (None, "lessons,planned-assignments,planned-to-dos", "planned-assignments,planned-to-dos"):
        try:
            data = dict(base_data)
            if types_guess is not None:
                data["types"] = types_guess
            raw_elements = session.json(url, data=data)
            parsed_elements = list(parse_planner_records(raw_elements, 'timetable'))
            _planner_diagnostics['timetable']['filter'] = types_guess or 'all'
            if parsed_elements:
                break
            empty_response = True
        except Exception as exc:  # noqa: BLE001 - next guess
            last_exc = exc
            rejected_records = rejected_records or bool(_planner_diagnostics.get('timetable', {}).get('skipped'))
            continue

    if not parsed_elements:
        if last_exc is not None and (rejected_records or not empty_response):
            raise last_exc  # every guess failed: let run() record it
        return {}

    by_date: dict[str, list[dict]] = {}

    for raw, pe in parsed_elements:
        raw = planner_details.public_payload(raw)
        posted_date = pe.period.date_time_from.date()

        course_names = ", ".join(str(c.name) for c in pe.courses) or None
        location = ", ".join(filter(None, (f"{l.title} {l.number}".strip() for l in pe.locations)))
        teacher = fmt_people(pe.organisers.users) if pe.organisers else ""
        groups = ", ".join(str(g.name) for g in pe.participants.groups) if pe.participants else ""
        title = str(pe.name)

        entry = {
            "moment_id": str(pe.id),
            "start": pe.period.date_time_from.strftime("%H:%M"),
            "end": pe.period.date_time_to.strftime("%H:%M"),
            "course": course_names or title,
            "classroom": location,
            "teacher": teacher,
            "groups": groups,
            "title": title,
            "detail_fields": [[path, val] for path, val in _flatten_raw(raw) if not _is_technical_field(path)],
            "source": "planner_api",
            "element_type": str(pe.planned_element_type),
        }

        by_date.setdefault(posted_date.isoformat(), []).append(entry)

    return by_date


def build_lessons(
    session: Smartschool,
    days_back: int,
    days_ahead: int,
    pending: list[dict],
    detail_fetcher: planner_details.DetailFetcher | None,
) -> list[dict]:
    today = date.today()
    start_date = today - timedelta(days=days_back)
    cutoff = today + timedelta(days=days_ahead)

    by_date: dict[str, list[dict]] = {}

    try:
        legacy = build_lessons_legacy(session, start_date, cutoff, pending)
        _planner_diagnostics['legacy'] = {'status': 'ok', 'parsed': sum(len(events) for events in legacy.values())}
        for d, events in legacy.items():
            by_date.setdefault(d, []).extend(events)
        if not legacy:
            print("  (legacy agenda endpoint returned nothing - your school is likely on the newer planner)")
    except Exception as exc:  # noqa: BLE001 - best effort
        _planner_diagnostics['legacy'] = {'status': 'failed', 'error': type(exc).__name__}
        print(f"  (legacy agenda fetch failed: {type(exc).__name__}; continuing with the newer planner API)", file=sys.stderr)

    try:
        planner = build_lessons_planner_api(session, start_date, cutoff, pending, detail_fetcher)
        for d, events in planner.items():
            by_date.setdefault(d, []).extend(events)
    except Exception as exc:  # noqa: BLE001 - best effort
        _planner_diagnostics.setdefault('planner', {}).update(status='failed', error=type(exc).__name__)
        print(f"  (newer planner API fetch failed: {type(exc).__name__})", file=sys.stderr)
        _fetch_errors["planner"] = exc

    days = []
    for d, events in sorted(by_date.items()):
        events.sort(key=lambda e: e["start"])
        days.append({"date": d, "events": events})

    return days


def build_future_tasks(session: Smartschool, pending: list[dict]) -> tuple[list[dict], list[dict]]:
    """Returns (days_for_display, flat_todos); due dates may be placeholders until the AI pass."""
    days = []
    todos = []
    for day in FutureTasks(session):
        posted_date = day.date
        courses = []
        for course in day.courses:
            tasks = []
            for t in course.items.tasks:
                text = t.description or ""
                due_date, corrected, source, needs_ai = resolve_due_date_sync(None, text, posted_date)
                task_record = {
                    "label": t.label,
                    "description": t.description,
                    "type": t.type,
                    "warning": bool(t.warning),
                    "due_date": due_date,
                    "due_date_corrected": corrected,
                    "due_date_source": source,
                }
                todo_record = {
                    "source_id": 'future:' + str(t.assignment_id) if str(t.assignment_id or '') not in ('', '0') else None,
                    "course": course.course_title,
                    "type": t.type,
                    "description": t.description,
                    "warning": bool(t.warning),
                    "posted_date": posted_date.isoformat(),
                    "due_date": due_date,
                    "due_date_corrected": corrected,
                    "due_date_source": source,
                    "source": "future_tasks",
                    "detail_fields": [["label", t.label]] if t.label else [],
                }
                if needs_ai:
                    _register_for_ai(pending, text, posted_date, [task_record, todo_record])
                tasks.append(task_record)
                todos.append(todo_record)
            courses.append(
                {
                    "course": course.course_title,
                    "materials": list(course.items.materials or []),
                    "tasks": tasks,
                }
            )
        days.append(
            {
                "date": posted_date.isoformat(),
                "pretty_date": day.pretty_date,
                "courses": courses,
            }
        )
    return days, todos


def resolve_ai_pending(pending: list[dict], gemini_api_key: str | None) -> dict | None:
    """One batched AI call for unresolved items; patches registered dicts in place.
    Returns a warning dict (see app_errors.gemini_warning) if Gemini had a problem, else None."""
    if _regex_active or not pending:
        return None

    if not gemini_api_key:
        print(f"  ({len(pending)} task(s) had no deadline in the text and no gemini_api_key is set - left on their posted date)")
        return None

    items = [(p["text"], p["posted"]) for p in pending]
    results, note = gemini_dates.extract_due_dates_batch(
        items,
        gemini_api_key,
        cache_file=DATA_DIR / "gemini_cache.json",
        usage_file=DATA_DIR / "gemini_usage.json",
    )
    if note:
        print(f"  {note}")

    for p, result_date in zip(pending, results):
        if not result_date:
            continue
        for entry in p["entries"]:
            entry["due_date"] = result_date.isoformat()
            entry["due_date_corrected"] = result_date != p['posted']
            entry["due_date_source"] = "ai"

    problem = gemini_dates.last_problem
    if problem:
        return app_errors.gemini_warning(problem.get("kind", "other"), problem.get("detail", ""))
    return None


def _num(text) -> float | None:
    try:
        return float(str(text).strip().replace(",", "."))
    except ValueError:
        return None


def parse_result(r: dict) -> dict | None:
    """One evaluation as a dict, parsed from raw JSON so one odd value can't lose every grade."""
    if not isinstance(r, dict) or r.get("deleted") or r.get("isPublished") is False:
        return None
    graphic = r.get("graphic") if isinstance(r.get("graphic"), dict) else {}
    gtype, desc, value = graphic.get("type"), str(graphic.get("description") or ""), graphic.get("value")
    score = maximum = percent = None
    text = ""
    if gtype == "percentage" and "/" in desc:
        left, _, right = desc.partition("/")
        score, maximum = _num(left), _num(right)
        if score is not None and maximum:
            percent = round(score / maximum * 100, 1)
    elif gtype == "percentage" and isinstance(value, (int, float)):
        percent = float(value)
    color = str(graphic.get("color") or "").strip().lower()
    if percent is None and gtype != "percentage":
        text = str(value if value not in (None, "") else desc).strip()
    courses = r.get("courses") if isinstance(r.get("courses"), list) else []
    course = next((c.get("name") for c in courses if isinstance(c, dict) and c.get("name")), "") or (
        (r.get("component") or {}).get("name") if isinstance(r.get("component"), dict) else ""
    )
    owner = r.get("gradebookOwner") if isinstance(r.get("gradebookOwner"), dict) else {}
    teacher = ((owner.get("name") or {}).get("startingWithFirstName") or "") if isinstance(owner.get("name"), dict) else ""
    period = (r.get("period") or {}).get("name", "") if isinstance(r.get("period"), dict) else ""
    feedback = [str(f.get("text")).strip() for f in (r.get("feedback") or []) if isinstance(f, dict) and f.get("text")]
    return {
        "id": str(r.get("identifier") or ""),
        "name": str(r.get("name") or "").strip(),
        "course": str(course or "Other"),
        "date": str(r.get("date") or "")[:10],
        "score": score,
        "max": maximum,
        "percent": percent,
        "text": text,
        "label": desc.strip() if desc.strip() and desc.strip() != text else "",
        "color": color,
        "counts": bool(r.get("doesCount", True)),
        "period": str(period),
        "teacher": str(teacher),
        "feedback": feedback,
    }


def fetch_results(session: Smartschool, max_pages: int = 4) -> tuple[list[dict], str]:
    """Grades, newest first. Never raises: returns ([], reason) if unavailable."""
    out: list[dict] = []
    try:
        for page in range(1, max_pages + 1):
            data = session.json(f"/results/api/v1/evaluations/?pageNumber={page}&itemsOnPage=50")
            if not isinstance(data, list):
                break
            out.extend(p for p in (parse_result(r) for r in data) if p)
            if len(data) < 50:
                break
    except Exception as exc:  # noqa: BLE001 - optional tab
        print(f"  (could not fetch grades: {exc})", file=sys.stderr)
        return out, f"Grades unavailable: {str(exc)[:120]}"
    out.sort(key=lambda x: x["date"], reverse=True)
    return out, ""


def fetch_assignment_types(session) -> list[dict]:
    if ApplicableAssignmentTypes is None:
        return []
    try:
        return [{'id': str(t.id), 'name': t.name, 'abbreviation': t.abbreviation,
                 'visible': t.is_visible} for t in ApplicableAssignmentTypes(session)]
    except Exception:  # Optional metadata must not stop a planner sync.
        return []


def lvs_since() -> date:
    today = date.today()
    return date(today.year if today.month >= 9 else today.year - 1, 9, 1)


def fetch_lvs(session) -> dict:
    """Optional, current-school-year overview. Never log personal LVS content."""
    since = lvs_since()
    until = date(since.year + 1, 8, 31)
    output = {'notes': [], 'absences': [], 'notes_error': '', 'absences_error': '', 'since': since.isoformat()}
    if StudentNotes is None or StudentAbsences is None:
        output['notes_error'] = output['absences_error'] = 'LVS requires smartschool 0.12.0 or newer. Update the app dependencies and restart.'
        return output
    try:
        for note in StudentNotes(session, since=since, until=until):
            if note.private:
                continue
            output['notes'].append({'id': str(note.item_id), 'title': note.title, 'category': note.cat_name,
                                    'date': note.date.isoformat() if note.date else '', 'author': note.author})
    except Exception:  # optional school/account permissions and network failures
        output['notes_error'] = 'Notes could not be loaded. Your school may not enable LVS access for this account. Try syncing again.'
    try:
        for absence in StudentAbsences(session, since=since, until=until):
            output['absences'].append({'id': str(absence.absent_id), 'date': absence.date.isoformat() if absence.date else '',
                                       'code': absence.code, 'description': absence.description,
                                       'part': str(absence.part_of_day or ''), 'info': absence.info})
    except Exception:
        output['absences_error'] = 'Absences could not be loaded. Access may be unavailable for this account. Try syncing again.'
    for key in ('notes', 'absences'):
        output[key].sort(key=lambda item: item['date'], reverse=True)
    return output


def fetch_lvs_note_detail(session, item_id: str) -> dict:
    if StudentNotes is None or StudentNoteDetails is None:
        raise RuntimeError('LVS requires smartschool 0.12.0 or newer')
    # Recheck visibility: a cached header must not grant access to a withdrawn/private note.
    since = lvs_since()
    if not any(str(note.item_id) == item_id and not note.private for note in StudentNotes(session, since=since, until=date(since.year + 1, 8, 31))):
        raise ValueError('Note is no longer available')
    detail = StudentNoteDetails(session, item_id=int(item_id)).get()
    if detail is None:
        raise ValueError('No note content')
    return {'text': detail.text, 'choice': detail.choice, 'fields': detail.fields,
            'date': detail.date.isoformat() if detail.date else '',
            'attachments': [{'name': attachment.file_name} for attachment in detail.attachments]}


@serial_sync
def run(days_back: int = 10, days_ahead: int = 21) -> dict:
    """Full sync; writes data/planner_data.json and returns the same data."""
    print("Logging in to Smartschool...")
    _fetch_errors.clear()
    _planner_diagnostics.clear()
    creds = credential_store.smartschool_credentials(ROOT / "credentials.yml")
    session = TimeoutSmartschool(creds)
    other_info = creds.other_info or {}
    gemini_api_key = str(other_info.get("gemini_api_key") or '').strip() or None
    global _regex_active
    _regex_active = task_state.date_checker_mode(ROOT, gemini_api_key) == 'local'
    detail_url_override = other_info.get("planner_detail_url") or None

    main_url = str(getattr(creds, "main_url", "") or "")
    current_account = credential_store.account_key({'main_url': main_url, 'username': creds.username})
    bad_address = app_errors.address_problem(main_url)
    if bad_address:
        raise app_errors.SyncError(bad_address["kind"], bad_address["title"], bad_address["message"], bad_address["hint"])

    # platform_id is a real request to the school, so it proves the address and login work.
    platform_id, user_id = None, None
    try:
        platform_id = session.platform_id
    except (KeyError, IndexError, TypeError):
        pass  # reached something that answered oddly (e.g. no courses): carry on, the final guard still checks
    except Exception as exc:  # noqa: BLE001
        info = app_errors.explain(exc, main_url)
        if info["kind"] == "unknown":
            info = {
                "kind": "network",
                "title": "Couldn't reach your school",
                "message": "Smartschool didn't answer the way it should.",
                "hint": app_errors.ADDRESS_HINT + " Then press Retry.",
                "details": info["details"],
            }
        raise app_errors.SyncError(info["kind"], info["title"], info["message"], info["hint"], info["details"]) from exc

    try:
        user_id = session.authenticated_user["id"]
    except Exception as exc:  # noqa: BLE001
        if platform_id is None:
            # nothing verified the school at all: blame the address/login rather than carry on blind
            info = app_errors.explain(exc, main_url)
            if info["kind"] != "unknown":
                raise app_errors.SyncError(
                    info["kind"], info["title"], info["message"], info["hint"], info["details"]
                ) from exc
        # school answered but no user id: carry on, later steps may still work

    DATA_DIR.mkdir(exist_ok=True)
    detail_fetcher = planner_details.DetailFetcher(
        session,
        DATA_DIR / "planner_detail_route.json",
        platform_id,
        user_id,
        custom_template=detail_url_override,
    )

    today = date.today()
    start_date = today - timedelta(days=days_back)
    cutoff = today + timedelta(days=days_ahead)
    try:
        previous = json.loads(OUTPUT_FILE.read_text(encoding='utf-8'))
        if user_id is None or not isinstance(previous, dict) or previous.get('account_key') != current_account or previous.get('main_url') != main_url or previous.get('user_id') != user_id:
            previous = {}
    except (OSError, ValueError):
        previous = {}

    pending: list[dict] = []

    print(f"Fetching lessons from {days_back} day(s) ago to {days_ahead} day(s) ahead...")
    lessons_by_day = build_lessons(session, days_back, days_ahead, pending, detail_fetcher)
    failed_sources = set()
    if 'planner' in _fetch_errors:
        failed_sources.add('planner_api')
    if _planner_diagnostics.get('legacy', {}).get('status') == 'failed':
        failed_sources.add('legacy_agenda')
    if failed_sources:
        by_date = {day['date']: day['events'] for day in lessons_by_day}
        for day in previous.get('days', []):
            if start_date.isoformat() <= day['date'] <= cutoff.isoformat():
                restored = [event for event in day['events'] if event.get('source') in failed_sources]
                if restored:
                    by_date.setdefault(day['date'], []).extend(restored)
        lessons_by_day = [{'date': day, 'events': sorted(events, key=lambda event: event['start'])} for day, events in sorted(by_date.items())]

    print("Fetching upcoming tasks/tests...")
    try:
        future_tasks, todos = build_future_tasks(session, pending)
    except Exception as exc:  # noqa: BLE001 - optional
        print(f"  (could not fetch the separate future-tasks list: {exc})", file=sys.stderr)
        print("  Continuing without it - lesson-level to-dos below still work.", file=sys.stderr)
        _fetch_errors['future_tasks'] = exc
        future_tasks = previous.get('future_tasks', [])
        todos = [task for task in previous.get('todos', []) if task.get('source') == 'future_tasks']

    if detail_fetcher.ok_count or detail_fetcher.fail_count:
        print(f"  (assignment detail fetch: {detail_fetcher.ok_count} ok, {detail_fetcher.fail_count} failed, route: {detail_fetcher.template or 'none found'})")

    print(f"Resolving due dates ({len(pending)} item(s) need a closer look)...")
    warnings: list[dict] = []
    ai_warning = resolve_ai_pending(pending, gemini_api_key)
    if ai_warning:
        warnings.append(ai_warning)

    # due dates final: merge lesson assignments into to-dos, assign ids
    for day in lessons_by_day:
        for ev in day["events"]:
            if ev["info"]:
                for a in ev["info"]["assignments"]:
                    a['body'] = a.get('body') or a.get('info') or ''
                    todos.append(
                        {
                            "course": ev["course"],
                            "type": a["type"],
                            "description": a["description"],
                            "body": a.get("body") or a.get("info") or '',
                            "attachments": a.get("attachments", []),
                            "weblinks": a.get("weblinks", []),
                            "warning": a["warning"],
                            "posted_date": day["date"],
                            "due_date": a["due_date"],
                            "due_date_corrected": a["due_date_corrected"],
                            "due_date_source": a.get("due_date_source", "none"),
                            "source": "lesson",
                            "detail_fields": a.get("detail_fields", []),
                            "moment_id": ev.get("moment_id"),
                            "element_source": ev.get("source"),
                            "element_type": ev.get("element_type"),
                            "id": a.get("id"),
                        }
                    )

    todos = assign_task_ids(todos, lessons_by_day, previous, [main_url, user_id if user_id is not None else creds.username])

    print("Fetching full timetable (all classes, even without to-dos)...")
    try:
        all_classes_by_date = build_all_classes_planner_api(session, start_date, cutoff)
    except Exception as exc:  # noqa: BLE001 - optional tab
        _planner_diagnostics.setdefault('timetable', {}).update(status='failed', error=type(exc).__name__)
        print(f"  (could not fetch the full timetable: {type(exc).__name__})", file=sys.stderr)
        _fetch_errors["timetable"] = exc
        all_classes_by_date = {day['date']: day['events'] for day in previous.get('all_classes', [])
                               if start_date.isoformat() <= day['date'] <= cutoff.isoformat()}
    all_classes = [
        {"date": d, "events": sorted(events, key=lambda e: e["start"])}
        for d, events in sorted(all_classes_by_date.items())
    ]
    skipped = sum(status.get('skipped', 0) for status in _planner_diagnostics.values())
    if not lessons_by_day or not all_classes or skipped or failed_sources or 'timetable' in _fetch_errors or 'future_tasks' in _fetch_errors:
        warnings.insert(0, {
            'source': 'planner', 'kind': 'planner_incomplete', 'title': 'Planner data may be incomplete',
            'message': f'Loaded {sum(len(day["events"]) for day in lessons_by_day)} schedule entries and '
                       f'{sum(len(day["events"]) for day in all_classes)} timetable entries. '
                       + (f'{skipped} records could not be read.' if skipped else 'Some planner sections returned no entries.'),
            'hint': 'Last saved entries are kept when a source fails. Retry syncing, or use Settings > Copy sync diagnostics for support.',
            'fix': False,
        })

    if "planner" in _fetch_errors and "timetable" in _fetch_errors and not lessons_by_day and not previous and not skipped:
        # Nothing core could be loaded. Don't pretend the sync worked and don't overwrite older data with empties.
        cause = _fetch_errors["planner"]
        info = app_errors.address_problem(main_url)
        if not info:
            explained = [(app_errors.explain(exc, main_url), exc) for exc in (_fetch_errors["planner"], _fetch_errors["timetable"])]
            info, cause = next(((i, e) for i, e in explained if i["kind"] != "unknown"), explained[0])
        if platform_id and info["title"] == app_errors.ADDRESS_NOT_FOUND_TITLE:
            info = {**info, "kind": "unknown"}  # the school did answer earlier, so don't blame the address
        if info["kind"] == "unknown":
            info = {
                "kind": "login",
                "title": "Couldn't load your planner",
                "message": "Smartschool didn't send back any planner data. This usually means the login was refused or Smartschool is having a problem.",
                "hint": app_errors.LOGIN_HINT + " If your details are right, wait a few minutes: Smartschool may be down.",
                "details": info["details"],
            }
        raise app_errors.SyncError(info["kind"], info["title"], info["message"], info["hint"], info["details"]) from cause

    if platform_id is None and not lessons_by_day and not todos and not all_classes:
        # Never confirmed the school and got nothing back at all: almost always a wrong address.
        raise app_errors.SyncError(
            "config",
            "Couldn't verify the school address",
            f"Smartschool{' (' + main_url + ')' if main_url else ''} didn't send back any account data.",
            app_errors.ADDRESS_HINT + " If it is right, check your username and password too.",
        )

    print("Fetching grades...")
    results, results_note = fetch_results(session)
    lvs = fetch_lvs(session)
    assignment_types = fetch_assignment_types(session)

    output = {
        "account_key": current_account,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "main_url": creds.main_url,
        "platform_id": platform_id,
        "user_id": user_id,
        "days": lessons_by_day,
        "future_tasks": future_tasks,
        "todos": todos,
        "all_classes": all_classes,
        "results": results,
        "results_note": results_note,
        "lvs": lvs,
        "assignment_types": assignment_types,
        "warnings": warnings,
        "diagnostics": {
            "app_version": __version__,
            "planner": {"from": start_date.isoformat(), "to": cutoff.isoformat(), "sources": _planner_diagnostics.copy()},
            "regex_parser_enabled": _regex_active,
            "gemini_configured": bool(gemini_api_key),
            "detail_fetch_status": detail_fetcher.status,
            "detail_fetch_route": detail_fetcher.template,
            "detail_fetch_attempts": detail_fetcher.attempts[-20:],
        },
    }

    if credential_store.account_key(credential_store.load_credentials(ROOT / 'credentials.yml')) != current_account:
        raise ValueError('Login details changed during sync. Please sync again.')
    write_snapshot(OUTPUT_FILE, output)
    print(f"Done. Wrote {OUTPUT_FILE}")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days-ahead", type=int, default=21, help="How many days ahead to pull the schedule for (default 21)")
    parser.add_argument("--days-back", type=int, default=10, help="How many days back to also pull, in case something was posted late (default 10)")
    args = parser.parse_args()
    try:
        run(days_back=args.days_back, days_ahead=args.days_ahead)
    except app_errors.SyncError as exc:
        print(f"\n{exc.title}: {exc.message}\n{exc.hint}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
