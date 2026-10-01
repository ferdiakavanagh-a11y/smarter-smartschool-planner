"""
scrapes all the data then writes it to the json file
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from smartschool import (
    FutureTasks,
    PathCredentials,
    PlannedElement,
    Smartschool,
    SmartschoolHours,
    SmartschoolLessons,
    SmartschoolMomentInfos,
)

from dutch_dates import resolve_due_date
import gemini_dates
import planner_details

# ---------------------------------------------------------------------------
# when set to true it uses the built in dutch_dates.py to set the deadlines and sends unchanged files to gemini. 
# when offline this is the only option
# ---------------------------------------------------------------------------
USE_REGEX_DEADLINE_PARSER = False


def get_root() -> Path:
    """Folder this program's files live in - the exe's own folder when
    packaged with PyInstaller, otherwise this script's folder."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


ROOT = get_root()
DATA_DIR = ROOT / "data"
OUTPUT_FILE = DATA_DIR / "planner_data.json"

# Status-flag values Smartschool uses for "nothing here" on a lesson.
# Anything else is treated as "there might be info worth fetching".
EMPTY_ISH = {"", "0", "false", "no", "none", None}


def looks_truthy(value) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() not in EMPTY_ISH


def fmt_person(name_obj) -> str:
    """PersonDescription -> a plain display name."""
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
    """Smartschool sometimes gives a real deadline field already (format unconfirmed
    for your school - could be empty, ISO, or DD/MM/YYYY). Try the sane options."""
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
    """
    The no-network part of figuring out a task's real due date. Smartschool
    tasks are often posted on one lesson day but actually due a different day
    mentioned only in the description text (e.g. "tegen donderdag").

    Priority: 1) an explicit structured deadline field, if Smartschool gives
    one and it parses cleanly (always on - this is a real field, not a guess),
    2) the free-text keyword parser in dutch_dates.py, ONLY if
    USE_REGEX_DEADLINE_PARSER is True.

    Returns (due_date_iso, was_corrected, source, needs_ai) - needs_ai=True
    means nothing was resolved here and this item should be sent to the AI
    batch pass (see gemini_dates.py), using the same free_text/reference_date.
    """
    structured = parse_structured_deadline(explicit_deadline)
    if structured:
        return structured.isoformat(), structured != reference_date, "structured", False

    if USE_REGEX_DEADLINE_PARSER:
        due_date, inferred = resolve_due_date(free_text, reference_date)
        if inferred:
            return due_date.isoformat(), True, "regex", False

    return reference_date.isoformat(), False, "none", True


def _register_for_ai(pending: list[dict], free_text: str, reference_date: date, entries: list[dict]) -> None:
    """Queues one or more dicts to be patched together once the AI batch pass
    resolves this item (entries are separate dict objects - e.g. a "task"
    display record and its matching "todo" record - that all need the same
    resulting due date written into them)."""
    if free_text and free_text.strip():
        pending.append({"text": free_text, "posted": reference_date, "entries": entries})


def stable_task_id(course: str, type_: str, description: str, due_date: str) -> str:
    """
    A stable id for a task that survives re-syncs (so "done" checkmarks persist
    even though we refetch and rebuild the whole todo list every run). Based on
    content, not on any Smartschool-assigned id, since not every source
    (future_tasks vs lesson-level assignments) reliably exposes the same kind
    of id. IMPORTANT: only call this once a task's due_date is FINAL (i.e.
    after the AI batch pass), or the id computed here won't match the one
    computed for the same task elsewhere once its due date changes.
    """
    raw = f"{course}|{type_}|{description}|{due_date}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _flatten_raw(obj, prefix: str = "") -> list[tuple[str, str]]:
    """
    Turns a nested JSON structure into a flat list of (path, value) pairs for
    every non-empty string/number leaf. Used for two things: (1) scanning for
    a deadline phrase anywhere in the data Smartschool actually sent back,
    not just under a handful of guessed field names, and (2) showing "every
    field Smartschool gave us" in the app's detail view, since the model this
    library exposes doesn't cover everything the raw API response contains.
    """
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


# Leaf field names that are pure backend plumbing, not anything a person
# looking at the Smartschool page would consider "information" - filtered out
# of the detail view so it isn't buried in noise, but NOT filtered out of the
# date-scanning text (harmless there, and erring toward finding the deadline
# matters more than a perfectly tidy scan).
_TECHNICAL_LEAF_NAMES = {
    "id", "platformid", "sort", "color", "resolvedstatus", "unconfirmed",
    "pinned", "isparticipant", "onlinesession", "plannedelementtype",
    "wholeday", "deadline",
}


def _is_technical_field(path: str) -> bool:
    last = path.rsplit(".", 1)[-1].split("[")[0].lower()
    return last in _TECHNICAL_LEAF_NAMES


def fetch_moment_info(
    session: Smartschool, moment_id: str, lesson_date: date, course: str, pending: list[dict]
) -> dict | None:
    try:
        info = SmartschoolMomentInfos(session, moment_id)
        # SmartschoolMomentInfos is iterable (yields one "class" element per xpath match);
        # take the first (there's only ever one for a given moment_id).
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
                    "id": None,  # filled in once due_date is final - see run()
                    "type": a.type,
                    "description": a.description,
                    "info": a.assignment_info,
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
    except Exception as exc:  # noqa: BLE001 - best-effort enrichment, never fatal
        print(f"  (could not fetch moment info for {moment_id}: {exc})", file=sys.stderr)
    return None


def build_lessons_legacy(
    session: Smartschool, start_date: date, cutoff: date, pending: list[dict]
) -> list[dict]:
    """
    Older Smartschool schools ("classic" agenda) expose lesson-by-lesson data
    through this XML dispatcher. Some schools have fully moved to the newer
    "Smartschool Next" planner - for those, this silently returns nothing
    (Smartschool itself answers with an empty body, not an error), which is
    why this is always paired with build_lessons_planner_api() below.

    Each call only covers a ~20 day forward window from the date you give it,
    so for longer ranges we call it a few times with different anchor dates
    and merge, deduping by moment_id.
    """
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
                "title": lesson.subject,  # the free-text title/explanation for this lesson
                "has_info": has_flagged_info,
                "info": None,  # filled in below if has_flagged_info
                "source": "legacy_agenda",
            }

            if has_flagged_info:
                print(f"  fetching detail for {entry['course']} on {lesson_date} ...")
                entry["info"] = fetch_moment_info(session, lesson.moment_id, lesson_date, entry["course"], pending)

            by_date.setdefault(lesson_date.isoformat(), []).append(entry)

        anchor += timedelta(days=18)  # slight overlap with the ~20 day window per call

    return by_date


def build_lessons_planner_api(
    session: Smartschool,
    start_date: date,
    cutoff: date,
    pending: list[dict],
    detail_fetcher: planner_details.DetailFetcher | None,
) -> dict[str, list[dict]]:
    """
    Fetches planner cards (assignments + to-dos) from the newer "Smartschool
    Next" REST API - the one that matches the card-style planner UI (title
    bar, teacher/groups/location sidebar, "Info voor de leerling" body).

    Unlike the legacy XML endpoint, this doesn't hand us a general timetable
    of every lesson - only cards that carry an assignment or to-do - which is
    exactly the data this tool cares about.

    IMPORTANT: this LIST endpoint only returns each card's title, never its
    body text - the actual "Info voor de leerling" content (where a real
    deadline sentence like "De deadline ... is VRIJDAG 25 SEPTEMBER" lives)
    has to be fetched per-item separately, which is what detail_fetcher does.
    """
    user_id = session.authenticated_user["id"]

    raw_elements = session.json(
        f"/planner/api/v1/planned-elements/user/{user_id}",
        data={"from": start_date.isoformat(), "to": cutoff.isoformat(), "types": "planned-assignments,planned-to-dos"},
    )

    by_date: dict[str, list[dict]] = {}

    for raw in raw_elements:
        pe = PlannedElement(**raw)
        posted_date = pe.period.date_time_from.date()

        course_names = ", ".join(str(c.name) for c in pe.courses) or None
        location = ", ".join(filter(None, (f"{l.title} {l.number}".strip() for l in pe.locations)))
        teacher = fmt_people(pe.organisers.users) if pe.organisers else ""
        groups = ", ".join(str(g.name) for g in pe.participants.groups) if pe.participants else ""
        title = str(pe.name)
        element_type = str(pe.planned_element_type)

        # Fetch the real body text ("Info voor de leerling") - see planner_details.py.
        detail_payload = None
        if detail_fetcher is not None:
            detail_payload = detail_fetcher.fetch(str(pe.id), element_type, posted_date, title)
        body_text = planner_details.extract_body(detail_payload, title) if detail_payload else ""

        # The task's description on cards stays the TITLE (plus anything the list
        # payload itself happens to carry). The fetched "Info voor de leerling"
        # text is kept separately as `body` and shown under the title - keeping
        # the description stable also keeps the checked-off ids stable.
        extra_text_parts = []
        for key in ("description", "content", "remark", "comment", "text", "body"):
            val = raw.get(key)
            if isinstance(val, str) and val.strip():
                extra_text_parts.append(val.strip())
        display_text = " ".join([title, *extra_text_parts]).strip()

        # What's scanned for a deadline phrase - the real body text (if we got
        # it) plus everything else Smartschool sent back for this element,
        # since a date can end up in an unexpected field too.
        raw_fields = _flatten_raw(raw)
        detail_raw_fields = _flatten_raw(detail_payload) if detail_payload else []
        scan_text = " ".join([display_text, body_text] + [v for _, v in raw_fields] + [v for _, v in detail_raw_fields])

        # If Smartschool itself marks this period as a deadline, trust its own
        # date over any text-guessing. Otherwise resolve what we can now and
        # queue the rest for the AI batch pass.
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
            "id": None,  # filled in once due_date is final - see run()
            "type": assignment_type,
            "description": display_text,
            "body": body_text,
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
    """
    Best-effort fetch of EVERY class period in the window, including ones with
    no assignment/to-do attached - i.e. a plain timetable, for the "All
    Classes" view. build_lessons_planner_api() above deliberately only asks
    for "planned-assignments,planned-to-dos" (matches what this tool mainly
    cares about); this tries broader/no type filtering to see if Smartschool
    hands back plain lessons too.

    NOTE: this is unverified against a live account as of writing - if it
    doesn't return anything beyond what the other tabs already show, that
    likely means either this school's plain lessons aren't exposed via this
    endpoint at all, or the type filter needs a different value than guessed
    here. Failing gracefully either way rather than crashing.
    """
    user_id = session.authenticated_user["id"]
    url = f"/planner/api/v1/planned-elements/user/{user_id}"
    base_data = {"from": start_date.isoformat(), "to": cutoff.isoformat()}

    raw_elements = None
    # Try a few guesses, broadest first, falling back to the known-working
    # filter (which just gives the same entries the other tabs already have).
    for types_guess in (None, "lessons,planned-assignments,planned-to-dos", "planned-assignments,planned-to-dos"):
        try:
            data = dict(base_data)
            if types_guess is not None:
                data["types"] = types_guess
            raw_elements = session.json(url, data=data)
            break
        except Exception:  # noqa: BLE001 - try the next guess
            continue

    if raw_elements is None:
        return {}

    by_date: dict[str, list[dict]] = {}

    for raw in raw_elements:
        try:
            pe = PlannedElement(**raw)
        except Exception:  # noqa: BLE001 - skip anything that doesn't fit the known shape
            continue
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
        for d, events in legacy.items():
            by_date.setdefault(d, []).extend(events)
        if not legacy:
            print("  (legacy agenda endpoint returned nothing - your school is likely on the newer planner)")
    except Exception as exc:  # noqa: BLE001 - best-effort, the planner API below may still work
        print(f"  (legacy agenda fetch failed, continuing with the newer planner API: {exc})", file=sys.stderr)

    try:
        planner = build_lessons_planner_api(session, start_date, cutoff, pending, detail_fetcher)
        for d, events in planner.items():
            by_date.setdefault(d, []).extend(events)
    except Exception as exc:  # noqa: BLE001 - best-effort, legacy source above may still have data
        print(f"  (newer planner API fetch failed: {exc})", file=sys.stderr)

    days = []
    for d, events in sorted(by_date.items()):
        events.sort(key=lambda e: e["start"])
        days.append({"date": d, "events": events})

    return days


def build_future_tasks(session: Smartschool, pending: list[dict]) -> tuple[list[dict], list[dict]]:
    """Returns (days_for_display, flat_todos) - due dates may still be
    placeholders pending the AI batch pass at this point."""
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


def resolve_ai_pending(pending: list[dict], gemini_api_key: str | None) -> None:
    """Runs the single batched AI call for everything the synchronous pass
    couldn't resolve, and patches every registered dict in place."""
    if not pending:
        return

    if not gemini_api_key:
        print(f"  ({len(pending)} task(s) had no deadline in the text and no gemini_api_key is set - left on their posted date)")
        return

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
            entry["due_date_corrected"] = True
            entry["due_date_source"] = "ai"


def run(days_back: int = 10, days_ahead: int = 21) -> dict:
    """
    Does the full sync and writes data/planner_data.json. Returns the same
    data as a dict, so callers (the CLI below, or the desktop app) can use it
    directly without re-reading the file.
    """
    print("Logging in to Smartschool...")
    creds = PathCredentials(str(ROOT / "credentials.yml"))
    session = Smartschool(creds)
    other_info = creds.other_info or {}
    gemini_api_key = other_info.get("gemini_api_key") or None
    detail_url_override = other_info.get("planner_detail_url") or None

    try:
        platform_id = session.platform_id
        user_id = session.authenticated_user["id"]
    except Exception:  # noqa: BLE001 - deep links / detail fetch are best-effort, never block a sync over them
        platform_id, user_id = None, None

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

    pending: list[dict] = []

    print(f"Fetching lessons from {days_back} day(s) ago to {days_ahead} day(s) ahead...")
    lessons_by_day = build_lessons(session, days_back, days_ahead, pending, detail_fetcher)

    print("Fetching upcoming tasks/tests...")
    try:
        future_tasks, todos = build_future_tasks(session, pending)
    except Exception as exc:  # noqa: BLE001 - this endpoint is optional/best-effort
        print(f"  (could not fetch the separate future-tasks list: {exc})", file=sys.stderr)
        print("  Continuing without it - lesson-level to-dos below still work.", file=sys.stderr)
        future_tasks, todos = [], []

    if detail_fetcher.ok_count or detail_fetcher.fail_count:
        print(f"  (assignment detail fetch: {detail_fetcher.ok_count} ok, {detail_fetcher.fail_count} failed, route: {detail_fetcher.template or 'none found'})")

    print(f"Resolving due dates ({len(pending)} item(s) need a closer look)...")
    resolve_ai_pending(pending, gemini_api_key)

    # Now that every due date is FINAL, fold lesson-level assignments into the
    # flat to-do list and assign stable ids (must happen after AI resolution -
    # the id is derived from the due date, so an id computed earlier would go
    # stale the moment AI corrects a date).
    for day in lessons_by_day:
        for ev in day["events"]:
            if ev["info"]:
                for a in ev["info"]["assignments"]:
                    a["id"] = stable_task_id(ev["course"], a["type"] or "", a["description"] or "", a["due_date"])
                    todos.append(
                        {
                            "course": ev["course"],
                            "type": a["type"],
                            "description": a["description"],
                            "body": a.get("body", ""),
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
                            "id": a["id"],
                        }
                    )

    for t in todos:
        if not t.get("id"):
            t["id"] = stable_task_id(t["course"], t.get("type") or "", t["description"] or "", t["due_date"])

    todos.sort(key=lambda t: t["due_date"])

    print("Fetching full timetable (all classes, even without to-dos)...")
    try:
        all_classes_by_date = build_all_classes_planner_api(session, start_date, cutoff)
    except Exception as exc:  # noqa: BLE001 - best-effort, optional tab
        print(f"  (could not fetch the full timetable: {exc})", file=sys.stderr)
        all_classes_by_date = {}
    all_classes = [
        {"date": d, "events": sorted(events, key=lambda e: e["start"])}
        for d, events in sorted(all_classes_by_date.items())
    ]

    output = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "main_url": creds.main_url,
        "platform_id": platform_id,
        "user_id": user_id,
        "days": lessons_by_day,
        "future_tasks": future_tasks,
        "todos": todos,
        "all_classes": all_classes,
        "diagnostics": {
            "regex_parser_enabled": USE_REGEX_DEADLINE_PARSER,
            "gemini_configured": bool(gemini_api_key),
            "detail_fetch_status": detail_fetcher.status,
            "detail_fetch_route": detail_fetcher.template,
            "detail_fetch_attempts": detail_fetcher.attempts[-20:],
        },
    }

    OUTPUT_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Done. Wrote {OUTPUT_FILE}")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days-ahead", type=int, default=21, help="How many days ahead to pull the schedule for (default 21)")
    parser.add_argument("--days-back", type=int, default=10, help="How many days back to also pull, in case something was posted late (default 10)")
    args = parser.parse_args()
    run(days_back=args.days_back, days_ahead=args.days_ahead)


if __name__ == "__main__":
    main()
