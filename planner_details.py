"""Fetches each assignment's body text ("Info voor de leerling"), which the list endpoint omits.
Tries likely routes (mirroring the web app's URLs) once and remembers the one that works;
override with `planner_detail_url` in credentials.yml."""

from __future__ import annotations

import html as html_lib
import json
import re
from datetime import date
from pathlib import Path

# placeholders: {id} element UUID, {platform_id}/{user_id}, {type} e.g. "planned-assignments", {date}
CANDIDATE_TEMPLATES = [
    # the library calls /lesson-content/api/v1/assignments/..., so text likely lives there
    "/lesson-content/api/v1/assignments/{platform_id}/{id}",
    "/lesson-content/api/v1/assignments/{id}",
    "/lesson-content/api/v1/assignments/{platform_id}/{id}/details",
    "/lesson-content/api/v1/planned-assignments/{platform_id}/{id}",
    "/lesson-content/api/v1/planned-assignments/{id}",
    "/planner/api/v1/planned-assignments/{platform_id}/{id}",
    "/planner/api/v1/planned-assignments/{id}",
    "/planner/api/v1/planned-elements/{platform_id}/{id}",
    "/planner/api/v1/planned-elements/{id}",
    "/planner/api/v1/planned-elements/user/{user_id}/{id}",
]

# keys likely holding task text
# bump when CANDIDATE_TEMPLATES changes so an old "nothing worked" result is retried
PROBE_VERSION = 2

_TEXTY_KEYS = (
    "description", "content", "text", "body", "info", "instruction",
    "html", "message", "remark", "comment", "summary", "explanation",
)
# keys that are never task text
_NOISE_KEYS = {
    "id", "platformid", "identifier", "pictureurl", "picturehash", "sort",
    "color", "icon", "type", "schedulecodes", "url", "href",
}

_TAG_RE = re.compile(r"<[a-zA-Z/!][^>]*>")
_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
_BLOCK_TAGS = ["p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "ul", "ol", "table"]


def flatten_json(obj, prefix: str = "") -> list[tuple[str, str]]:
    """Non-empty string/number leaves of nested JSON as (path, value)."""
    out: list[tuple[str, str]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.extend(flatten_json(v, f"{prefix}.{k}" if prefix else k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.extend(flatten_json(v, f"{prefix}[{i}]"))
    elif isinstance(obj, str):
        s = obj.strip()
        if s:
            out.append((prefix, s))
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        out.append((prefix, str(obj)))
    return out


def html_to_text(value: str) -> str:
    """HTML description -> plain text; keeps paragraph breaks, not inline-tag splits."""
    if not value:
        return ""
    text = value
    if _TAG_RE.search(value):
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(value, "html.parser")
            for br in soup.find_all("br"):
                br.replace_with("\n")
            for li in soup.find_all("li"):
                li.insert(0, "\u2022 ")
            for tag in soup.find_all(_BLOCK_TAGS):
                tag.insert_before("\n")
                tag.append("\n")
            text = soup.get_text("")
        except Exception:  # noqa: BLE001 - crude tag strip
            text = _TAG_RE.sub(" ", value)
    text = html_lib.unescape(text).replace("\xa0", " ")

    out: list[str] = []
    blank = 0
    for line in (ln.strip() for ln in text.splitlines()):
        if line == "":
            blank += 1
            if blank == 1:
                out.append("")
        else:
            blank = 0
            out.append(re.sub(r"[ \t]{2,}", " ", line))
    return "\n".join(out).strip()


def _last_key(path: str) -> str:
    return path.rsplit(".", 1)[-1].split("[")[0].lower()


# "Info voor de leerling" = top-level `publicInfo`; ignore `info`, `privateInfo`, `linkedPlannedElement`
_PRIMARY_KEYS = ("publicInfo", "info")


def extract_body(payload, title: str) -> str:
    """Task text ("Info voor de leerling") from a detail payload."""
    if isinstance(payload, dict) and any(k in payload for k in _PRIMARY_KEYS):
        for key in _PRIMARY_KEYS:
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                text = html_to_text(value)
                if text and text.strip().lower() != (title or "").strip().lower():
                    return text
        return ""  # no info text

    # unknown shape: guess from field names
    if isinstance(payload, dict):
        payload = {k: v for k, v in payload.items() if k != "linkedPlannedElement"}
    flat = flatten_json(payload)
    title_l = (title or "").strip().lower()

    def usable(path: str, value: str) -> bool:
        if _last_key(path) in _NOISE_KEYS:
            return False
        if value.strip().lower() == title_l:
            return False
        if _UUID_RE.match(value) or value.startswith(("http://", "https://")):
            return False
        return len(value) >= 3

    texty = [(p, v) for p, v in flat if usable(p, v) and any(k in _last_key(p) for k in _TEXTY_KEYS)]
    if not texty:  # any long non-plumbing string
        texty = [(p, v) for p, v in flat if usable(p, v) and len(v) > 80]

    seen: set[str] = set()
    parts: list[str] = []
    for _, v in texty:
        t = html_to_text(v)
        if t and t not in seen:
            seen.add(t)
            parts.append(t)
    return "\n\n".join(parts)


class DetailFetcher:
    """Fetches detail payloads, discovering the working route once."""

    def __init__(self, session, state_file: Path, platform_id, user_id, custom_template: str | None = None):
        self.session = session
        self.state_file = state_file
        self.platform_id = platform_id
        self.user_id = user_id
        self.custom_template = custom_template or None
        self.template: str | None = None
        self.disabled = platform_id is None or user_id is None
        self.ok_count = 0
        self.fail_count = 0
        self.attempts: list[str] = []
        self._cache: dict[str, dict | None] = {}
        self._probed_this_run = False
        self.route_is_saved = False  # route came from the saved file
        self._type_ok: dict[str, int] = {}
        self._type_fail: dict[str, int] = {}
        self._load_state()

    # -- saved route --
    def _load_state(self) -> None:
        if self.custom_template:
            self.template = self.custom_template
            return
        try:
            state = json.loads(self.state_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if state.get("template"):
            self.template = state["template"]
            self.route_is_saved = True
            # saved routes were learned on assignments; other types swap their own type into the URL
            self.template = self.template.replace("/planned-assignments/", "/{type}/")
        elif state.get("failed_on") == date.today().isoformat() and state.get("probe_version") == PROBE_VERSION:
            self.disabled = True  # tried today already

    def _save_state(self, template: str | None, failed: bool) -> None:
        if self.custom_template or (self.route_is_saved and template is None):
            return  # never overwrite a working route with a failure
        try:
            self.state_file.parent.mkdir(exist_ok=True)
            self.state_file.write_text(
                json.dumps({"template": template, "failed_on": date.today().isoformat() if failed else None, "probe_version": PROBE_VERSION}),
                encoding="utf-8",
            )
        except OSError:
            pass

    def _write_probe_log(self) -> None:
        try:
            (self.state_file.parent / "detail_probe.log").write_text("\n".join(self.attempts), encoding="utf-8")
        except OSError:
            pass

    # -- fetching --
    def _get(self, template: str, ctx: dict) -> dict | None:
        try:
            url = template.format(**ctx)
        except (KeyError, IndexError) as exc:
            self.attempts.append(f"{template} -> bad placeholder {exc}")
            return None
        try:
            payload = self.session.json(url)
        except Exception as exc:  # noqa: BLE001 - expected while probing
            resp = exc.args[1] if len(getattr(exc, "args", ())) > 1 else None
            status = getattr(resp, "status_code", None)
            self.attempts.append(f"{url} -> {f'HTTP {status}' if status else type(exc).__name__}: {str(exc)[:100]}")
            return None
        if isinstance(payload, list) and len(payload) == 1:
            payload = payload[0]
        if not isinstance(payload, dict) or not payload:
            self.attempts.append(f"{url} -> 200 but empty/unexpected payload")
            return None
        dumped = json.dumps(payload, ensure_ascii=False)
        title_l = (ctx.get("title") or "").strip().lower()
        if ctx["id"] not in dumped and not (title_l and title_l in dumped.lower()):
            self.attempts.append(f"{url} -> 200 but payload mentions neither this element's id nor its title")
            return None
        self.attempts.append(f"{url} -> OK")
        return payload

    def fetch(self, element_id: str, element_type: str, posted_date: date, title: str = "") -> dict | None:
        if element_id in self._cache:
            return self._cache[element_id]
        if self.disabled:
            return None

        ctx = {
            "id": element_id,
            "platform_id": self.platform_id,
            "user_id": self.user_id,
            "type": element_type,
            "date": posted_date.isoformat(),
            "title": title,
        }

        # stop asking a type after a few failures with no success
        if self._type_fail.get(element_type, 0) >= 3 and not self._type_ok.get(element_type):
            self._cache[element_id] = None
            return None

        payload = None
        if self.template:
            payload = self._get(self.template, ctx)
        elif not self.custom_template and element_type == "planned-assignments":
            # no route yet: probe on an assignment
            self._probed_this_run = True
            for candidate in CANDIDATE_TEMPLATES:
                payload = self._get(candidate, ctx)
                if payload is not None:
                    self.template = candidate
                    self._save_state(candidate, failed=False)
                    break
            if payload is None:
                self.disabled = True
                self._save_state(None, failed=True)
                self._write_probe_log()

        if payload is None:
            self.fail_count += 1
            self._type_fail[element_type] = self._type_fail.get(element_type, 0) + 1
        else:
            self.ok_count += 1
            self._type_ok[element_type] = self._type_ok.get(element_type, 0) + 1
            if self.template and not self.route_is_saved and not self.custom_template:
                pass  # saved on discovery
        self._cache[element_id] = payload
        return payload

    @property
    def status(self) -> str:
        if self.ok_count:
            return "ok"
        if self.disabled or self.fail_count:
            if self.route_is_saved:
                self.attempts.append("saved route returned nothing for any task this sync")
                self._write_probe_log()
            return "unavailable"
        return "n/a"


# ---- route discovery helpers ----
_API_STR_RE = re.compile(r"""["'`]((?:https?://[^"'`\s/]+)?/?[\w\-./]*api/v\d+/[\w\-./${}:+]*)["'`]""")

def api_paths_from_js(js_text: str) -> set[str]:
    """API paths in a JS bundle; `${x}`/`:x` become `{}`, trailing-slash fragments kept."""
    found: set[str] = set()
    for m in _API_STR_RE.finditer(js_text):
        path = re.sub(r"^https?://[^/]+", "", m.group(1))
        path = re.sub(r"\$\{[^}]*\}", "{}", path)
        path = re.sub(r"/:[A-Za-z_]\w*", "/{}", path)
        if not path.startswith("/"):
            path = "/" + path
        found.add(path)
    return found


def expand_path(path: str, ctx: dict) -> list[str]:
    """Concrete URLs from a path, filling placeholders with every ordering of platform/element/user id."""
    from itertools import permutations

    values = [str(ctx["platform_id"]), str(ctx["id"]), str(ctx["user_id"])]
    if ctx.get("type") and "{}/" in path[:2] + path:  # only when a type slot is possible
        values.append(str(ctx["type"]))
    n = path.count("{}")
    urls: list[str] = []
    if n == 0:
        if path.endswith("/"):  # fragment: rest appended in JS
            urls += [path + values[1], path + f"{values[0]}/{values[1]}"]
        else:
            urls.append(path)
        return urls
    if n > 3:
        return []
    for combo in permutations(values, n):
        out = path
        for v in combo:
            out = out.replace("{}", v, 1)
        urls.append(out)
    return urls


# ---- fragment harvesting: collect URL tails the JS appends to a base ----
_FRAGMENT_RE = re.compile(r"""[`"']([^`"'\s]{0,80}(?:assign|to-?do|planned|detail)[^`"'\s]{0,80})[`"']""", re.I)


def fragments_from_js(js_text: str) -> set[str]:
    """Path-like literals about assignments/planned items/to-dos/details, placeholders as `{}`, base stripped."""
    out: set[str] = set()
    for m in _FRAGMENT_RE.finditer(js_text):
        frag = m.group(1)
        if "/" not in frag or frag.startswith(("http", "data:")) or "api/v" in frag or "." in frag.split("/")[0]:
            continue
        frag = re.sub(r"\$\{[^}]*\}", "{}", frag)
        frag = re.sub(r"/:[A-Za-z_]\w*", "/{}", frag)
        frag = re.sub(r"^(?:\{\}/?)+", "", frag.replace("{}{}", "{}")).strip("/")  # drop a leading ${baseUrl}
        if re.fullmatch(r"[\w\-{}/]+", frag) and frag.count("{}") <= 3:
            out.add(frag)
    return out


def snippets_from_js(js_text: str, needles=("assignments", "planned-elements"), width: int = 170, limit: int = 40) -> list[str]:
    """Text around each mention of a needle."""
    found: list[str] = []
    for needle in needles:
        for m in re.finditer(re.escape(needle), js_text):
            a, b = max(0, m.start() - width), min(len(js_text), m.end() + width)
            found.append(js_text[a:b].replace("\n", " "))
            if len(found) >= limit:
                return found
    return found


# ---- route table: every api.<service>.baseUrl}<tail> call ----
_ELEMENT_TYPE_NAMES = {
    "ASSIGNMENT": "planned-assignments", "ACTIVITY": "planned-activities", "LESSON": "planned-lessons",
    "MEETING": "planned-meetings", "TODO": "planned-to-dos", "GENERIC": "planned-generics",
    "PLACEHOLDER": "planned-placeholders", "ROUTINE": "planned-routines",
    "SCHOOL_ACTIVITY": "planned-school-activities",
}
_ROUTE_RE = re.compile(r"""(?:\.api\.([A-Za-z]+)\.baseUrl|\bBASE_URL|\bbaseUrl)\}([^`"'\s]*)""")
_UNSAFE_WORDS = re.compile(
    r"delete|trash|resolve|replace|reschedul|confirm|create|copy|move|pin|publish|send|remove|restore|undo|save|"
    r"update|edit|add|cancel|reject|accept|import|upload|hide|share|label|order|sort|plan-", re.I)


def _kebab(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


def routes_from_js(js_text: str) -> set[tuple[str, str]]:
    """(service, tail) pairs for ${...baseUrl}<tail> calls; service may be "".
    PLE_ASSIGNMENT_ELEMENT_TYPE -> "planned-assignments", other ${x} -> `{}`, queries dropped."""
    out: set[tuple[str, str]] = set()
    for m in _ROUTE_RE.finditer(js_text):
        service, tail = _kebab(m.group(1) or ""), m.group(2)
        tail = tail.split("?")[0]
        tail = re.sub(r"\$\{[^}]*PLE_(\w+?)_(?:ELEMENT_)?TYPE\}",
                      lambda mm: _ELEMENT_TYPE_NAMES.get(mm.group(1), "{}"), tail)
        tail = re.sub(r"\$\{[^}]*\}", "{}", tail).strip("/")
        if tail and re.fullmatch(r"[\w\-{}/]+", tail) and tail.count("{}") <= 3:
            out.add((service, tail))
    return out


def route_is_safe_to_try(tail: str) -> bool:
    return not _UNSAFE_WORDS.search(tail)


# ---- attachments and weblinks ----
_LINK_NAME_KEYS = ("name", "title", "fileName", "filename", "label", "description", "displayName")
_LINK_URL_KEYS = ("url", "href", "link", "downloadUrl", "fileUrl", "uri")


def _link_entry(item) -> dict | None:
    if isinstance(item, str):
        item = {"url": item} if item.startswith(("http://", "https://")) else {"name": item}
    if not isinstance(item, dict):
        return None
    name = next((str(item[k]).strip() for k in _LINK_NAME_KEYS if isinstance(item.get(k), str) and item[k].strip()), "")
    url = next((str(item[k]).strip() for k in _LINK_URL_KEYS if isinstance(item.get(k), str) and item[k].strip()), "")
    size = item.get("size") if isinstance(item.get("size"), (int, float)) else item.get("fileSize")
    if not name and not url:
        return None
    return {"name": name or url, "url": url if url.startswith(("http://", "https://")) else "", "size": size if isinstance(size, (int, float)) else None}


def extract_links(payload) -> dict:
    """{"attachments": [...], "weblinks": [...]} from the task's own top-level lists (shape unverified, read defensively)."""
    out = {"attachments": [], "weblinks": []}
    if not isinstance(payload, dict):
        return out
    for key in ("attachments", "weblinks"):
        items = payload.get(key)
        if isinstance(items, list):
            out[key] = [e for e in (_link_entry(i) for i in items) if e]
    return out
