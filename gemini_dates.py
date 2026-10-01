"""
Deadline detection using Google's Gemini API (Google AI Studio free tier).

Everything a sync wants to know is sent in ONE request (chunked at 40 tasks,
so a sync is normally a single call), and every answer is cached on disk so
unchanged tasks are never asked about twice. A persistent PER-MODEL rate limiter
keeps usage under the free-tier limits below across syncs and app restarts, and
if a model is overloaded (503) or used up (429) the next model in MODEL_CHAIN is
tried instead of retrying the broken one.

Design rules (because a wrong date is worse than no date):
  * the model is told to answer null unless the text itself states a deadline
  * an answer equal to (or before) the posted date is discarded - that's not a
    correction, it's the model defaulting
  * an answer more than MAX_DAYS_AHEAD days out is discarded as implausible
  * anything that fails just leaves the task on its posted date
"""

from __future__ import annotations

import hashlib
import json
import random
import re
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# ---- Models, tried in this order --------------------------------------------
# Free-tier limits are PER MODEL (check https://aistudio.google.com/rate-limit -
# Google changes them often). Numbers below are from your own dashboard:
#   * Flash-Lite models: 15 requests/min, 500 requests/day  <- plenty for this job
#   * full "Flash" models:  5 requests/min,  20 requests/day  <- used up after a few syncs
# So the cheap Lite models go first (extracting a date from a sentence doesn't need
# a big model), and the full Flash models are only a last resort. Each model has
# its own quota, so falling through the list also multiplies what you can use.
# If a model id ever 404s it is skipped for the day, so a stale entry is harmless.
MODEL_CHAIN = [
    # (model id,              rpm, tpm,     rpd)
    ("gemini-3.1-flash-lite", 15, 250_000, 500),
    ("gemini-3.5-flash-lite", 15, 250_000, 500),
    ("gemini-3.8-flash",       5, 250_000,  20),
    ("gemini-3.7-flash",       5, 250_000,  20),
    ("gemini-3.6-flash",       5, 250_000,  20),
    ("gemini-3.5-flash",       5, 250_000,  20),
]
SAFETY_FACTOR = 0.8                  # stay at 80% of every limit above

MAX_ITEMS_PER_REQUEST = 40           # tasks per request (a sync is normally exactly 1 request)
MAX_TEXT_CHARS = 1500                # per task; keeps prompts small
MAX_DAYS_AHEAD = 120                 # deadlines further out than this are treated as nonsense
REQUEST_TIMEOUT_MS = 60_000          # a hung connection must fail, not block the sync forever
TRANSIENT_RETRY_DELAY = 3            # seconds before the ONE same-model retry after a 5xx
MAX_SLOT_WAIT_SECONDS = 15           # wait at most this long for a per-minute slot, else try the next model
COOLDOWN_AFTER_429_SECONDS = 65      # a per-minute 429 -> skip that model for a bit

# Skip tasks whose text has nothing date-like in it at all (saves quota; the
# answer would be "null" anyway). Set False to send every task.
SKIP_TEXT_WITHOUT_DATE_HINTS = True

_client = None
_client_key = None
_last_model_used = ""

_HINT_RE = re.compile(
    r"\d|maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag|monday|tuesday|wednesday|thursday|"
    r"friday|saturday|sunday|lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche|montag|dienstag|mittwoch|"
    r"donnerstag|freitag|samstag|sonntag|januari|februari|maart|april|mei|juni|juli|augustus|september|"
    r"oktober|november|december|january|february|march|june|july|august|october|janvier|f[eé]vrier|mars|"
    r"avril|mai|juin|juillet|ao[uû]t|septembre|octobre|novembre|d[eé]cembre|januar|februar|m[aä]rz|dezember|"
    r"vandaag|morgen|overmorgen|volgende|week|deadline|tegen|uiterlijk|today|tomorrow|next|due|demain|"
    r"prochain|semaine|heute|[uü]bermorgen|n[aä]chste|woche|frist|abgabe",
    re.IGNORECASE,
)


def looks_worth_asking(text: str) -> bool:
    return len(text.strip()) >= 12 and bool(_HINT_RE.search(text))


# ---- persistent, per-model rate limiter ----------------------------------------
def _pacific_day() -> str:
    try:
        from zoneinfo import ZoneInfo

        return datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()
    except Exception:  # noqa: BLE001 - no tz database (needs the 'tzdata' package on Windows)
        return (datetime.now(timezone.utc) - timedelta(hours=8)).date().isoformat()


class LimitReached(Exception):
    pass


class AllModelsFailed(Exception):
    pass


class UsageLimiter:
    """Per-model requests/min, tokens/min and requests/day (Pacific day), saved to disk.

    Also remembers, for the rest of the day, models that are used up or don't exist,
    and short cooldowns after a per-minute 429.
    """

    def __init__(self, path: Path | None):
        self.path = path
        self.state: dict = {"version": 2, "day": _pacific_day(), "models": {}}
        if path:
            try:
                loaded = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict) and loaded.get("version") == 2:
                    self.state.update(loaded)
            except (OSError, json.JSONDecodeError):
                pass

    @staticmethod
    def limits(model: str) -> tuple[int, int, int]:
        for name, rpm, tpm, rpd in MODEL_CHAIN:
            if name == model:
                return (
                    max(1, int(rpm * SAFETY_FACTOR)),
                    int(tpm * SAFETY_FACTOR),
                    max(1, int(rpd * SAFETY_FACTOR)),
                )
        return 4, 200_000, 16

    def _m(self, model: str, now: float) -> dict:
        today = _pacific_day()
        if self.state.get("day") != today:  # new Pacific day: everything resets
            self.state = {"version": 2, "day": today, "models": {}}
        m = self.state["models"].setdefault(
            model, {"requests_today": 0, "recent": [], "blocked_today": "", "cooldown_until": 0}
        )
        m["recent"] = [r for r in m.get("recent", []) if now - r[0] < 60]
        return m

    def _save(self) -> None:
        if not self.path:
            return
        try:
            self.path.parent.mkdir(exist_ok=True)
            self.path.write_text(json.dumps(self.state), encoding="utf-8")
        except OSError:
            pass

    def wait_for_slot(self, model: str, est_tokens: int) -> None:
        """Brief wait until `model` has room; raises LimitReached if it can't be used right now."""
        max_rpm, max_tpm, max_rpd = self.limits(model)
        deadline = time.time() + MAX_SLOT_WAIT_SECONDS
        while True:
            now = time.time()
            m = self._m(model, now)
            if m["blocked_today"]:
                raise LimitReached(m["blocked_today"])
            if m["requests_today"] >= max_rpd:
                raise LimitReached(f"daily limit reached ({m['requests_today']} today)")
            if m["cooldown_until"] > now:
                raise LimitReached("cooling down after a rate-limit response")
            recent = m["recent"]
            if len(recent) < max_rpm and sum(r[1] for r in recent) + est_tokens <= max_tpm:
                return
            wait = (60 - (now - recent[0][0]) + 0.5) if recent else 1.0
            if now + wait > deadline:
                raise LimitReached("per-minute limit reached")
            time.sleep(max(wait, 0.5))

    def record(self, model: str, est_tokens: int) -> None:
        # Failed requests can count toward Google's quota too, so record every attempt.
        now = time.time()
        m = self._m(model, now)
        m["recent"].append([now, est_tokens])
        m["requests_today"] += 1
        self._save()

    def block_today(self, model: str, reason: str) -> None:
        self._m(model, time.time())["blocked_today"] = reason
        self._save()

    def cooldown(self, model: str, seconds: float) -> None:
        self._m(model, time.time())["cooldown_until"] = time.time() + seconds
        self._save()


# ---- client ----------------------------------------------------------------------
def _get_client(api_key: str):
    global _client, _client_key
    if _client is None or _client_key != api_key:
        from google import genai  # lazy: only needed when a key is configured

        try:
            _client = genai.Client(api_key=api_key, http_options={"timeout": REQUEST_TIMEOUT_MS})
        except Exception:  # noqa: BLE001 - older SDK without http_options support
            _client = genai.Client(api_key=api_key)
        _client_key = api_key
    return _client


def _error_code(exc: Exception) -> int | None:
    for attr in ("code", "status_code"):
        v = getattr(exc, attr, None)
        if isinstance(v, int):
            return v
    m = re.search(r"\b([45]\d\d)\b", str(exc))
    return int(m.group(1)) if m else None


def _is_transient(exc: Exception, code: int | None) -> bool:
    """503 'model is overloaded' (and friends), plus timeouts/dropped connections."""
    if code in (500, 502, 503, 504):
        return True
    text = f"{type(exc).__name__} {exc}".lower()
    return code is None and any(w in text for w in ("timeout", "timed out", "unavailable", "overloaded", "connection"))


def _generate(client, prompt: str, limiter: UsageLimiter):
    """
    One request, walking down MODEL_CHAIN until a model answers.
    Returns (response, model_used). Raises AllModelsFailed / LimitReached / a real error.

    Why this shape (see also Google's docs on 503 UNAVAILABLE): a 503 means THAT model
    is overloaded right now, regardless of your quota - hammering it with retries
    only burns your daily requests. So: one short retry, then move to the next model.
    """
    global _last_model_used
    est_tokens = len(prompt) // 3 + 500
    problems: list[str] = []
    limit_only = True  # True while every model was skipped purely because of our own limits

    for model, *_ in MODEL_CHAIN:
        for attempt in range(2):
            try:
                limiter.wait_for_slot(model, est_tokens)
            except LimitReached as exc:
                problems.append(f"{model}: {exc}")
                break
            limit_only = False
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config={"response_mime_type": "application/json", "temperature": 0},
                )
                limiter.record(model, est_tokens)
                _last_model_used = model
                return response, model
            except Exception as exc:  # noqa: BLE001
                limiter.record(model, est_tokens)
                code = _error_code(exc)
                if _is_transient(exc, code):
                    if attempt == 0:
                        time.sleep(TRANSIENT_RETRY_DELAY + random.random() * 2)
                        continue
                    problems.append(f"{model}: overloaded/unavailable ({code or 'timeout'})")
                    break
                if code == 429:
                    flat = str(exc).lower().replace(" ", "").replace("_", "")
                    if "perday" in flat or "requestsperday" in flat:
                        limiter.block_today(model, "daily quota used up")
                    else:
                        limiter.cooldown(model, COOLDOWN_AFTER_429_SECONDS)
                    problems.append(f"{model}: rate limited (429)")
                    break
                if code == 404:
                    limiter.block_today(model, "model not available for this key")
                    problems.append(f"{model}: not found (404)")
                    break
                raise  # 400/401/403 etc: our request or key is wrong - another model won't fix it

    if limit_only:
        raise LimitReached("; ".join(problems) or "no model available")
    raise AllModelsFailed("; ".join(problems))


# ---- prompt / parsing ------------------------------------------------------------
PROMPT = """You extract homework/assignment DEADLINES from teachers' task descriptions. The texts are mostly Dutch, sometimes French, German or English.

For each numbered item you get the day the task was posted (with its weekday) and the task text. Decide the date the work must be handed in / is due / the test or presentation takes place.

Rules:
- Only give a date if the text itself states or clearly implies it, e.g. "De deadline voor deze opdracht is VRIJDAG 25 SEPTEMBER", "tegen donderdag", "date limite : lundi 5/10", "test op 3/10", "volgende week dinsdag".
- Resolve weekday names and relative phrases against the posted date: a weekday name means its next occurrence AFTER the posted date. Use the posted date's year unless the text says otherwise.
- If several dates appear, choose the actual deadline - not the date the task was given, not a lesson date. A time of day such as "16u10" is not a date.
- If the text contains no deadline, or you are unsure, answer null. NEVER answer with the posted date itself and never guess.

Answer with ONLY a JSON array, one object per item, exactly in this shape:
[{"id": 0, "due_date": "YYYY-MM-DD", "confidence": "high"}, {"id": 1, "due_date": null, "confidence": "high"}]

Items:
__ITEMS__
"""


def _cache_key(text: str, posted: date) -> str:
    return hashlib.sha1(f"{posted.isoformat()}|{text[:MAX_TEXT_CHARS]}".encode("utf-8")).hexdigest()[:20]


def _load_cache(path: Path | None) -> dict:
    if not path:
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_cache(path: Path | None, cache: dict) -> None:
    if not path:
        return
    try:
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(cache), encoding="utf-8")
    except OSError:
        pass


def _validated(raw_date, confidence, posted: date) -> date | None:
    """Only a confident, plausible date that actually differs from the posted day counts."""
    if not raw_date or raw_date == "null" or confidence != "high":
        return None
    try:
        d = date.fromisoformat(str(raw_date)[:10])
    except ValueError:
        return None
    if d <= posted or d > posted + timedelta(days=MAX_DAYS_AHEAD):
        return None
    return d


def _parse_response(text: str) -> dict[int, tuple] | None:
    try:
        data = json.loads(text)
    except (TypeError, json.JSONDecodeError):
        return None
    if isinstance(data, dict):
        data = data.get("results") or data.get("items") or []
    if not isinstance(data, list):
        return None
    out: dict[int, tuple] = {}
    for row in data:
        if isinstance(row, dict) and "id" in row:
            try:
                out[int(row["id"])] = (row.get("due_date"), row.get("confidence"))
            except (TypeError, ValueError):
                continue
    return out


# ---- public API ------------------------------------------------------------------
def extract_due_dates_batch(
    items: list[tuple[str, date]],
    api_key: str | None,
    cache_file: Path | None = None,
    usage_file: Path | None = None,
) -> tuple[list[date | None], str]:
    """
    items: [(task_text, posted_date), ...]
    Returns (results, note): results[i] is the detected deadline for items[i] or
    None; note is a short human-readable summary (or "" if nothing to say).
    """
    results: list[date | None] = [None] * len(items)
    if not items or not api_key:
        return results, ""

    cache = _load_cache(cache_file)
    pending: dict[str, list[int]] = {}
    pending_info: dict[str, tuple[str, date]] = {}
    cached_hits = 0

    for i, (text, posted) in enumerate(items):
        text = (text or "").strip()
        if not text or (SKIP_TEXT_WITHOUT_DATE_HINTS and not looks_worth_asking(text)):
            continue
        key = _cache_key(text, posted)
        if key in cache:
            cached_hits += 1
            results[i] = _validated(cache[key], "high", posted) if cache[key] else None
            continue
        pending.setdefault(key, []).append(i)
        pending_info[key] = (text[:MAX_TEXT_CHARS], posted)

    if not pending:
        return results, ""

    try:
        client = _get_client(api_key)
    except ImportError:
        return results, "AI deadline detection is on, but the 'google-genai' package isn't installed (pip install google-genai)."
    except Exception as exc:  # noqa: BLE001
        return results, f"AI deadline detection couldn't start: {exc}"

    limiter = UsageLimiter(usage_file)
    keys = list(pending)
    requests_made = 0
    models_used: set[str] = set()
    found = 0
    problem = ""

    for start in range(0, len(keys), MAX_ITEMS_PER_REQUEST):
        chunk = keys[start : start + MAX_ITEMS_PER_REQUEST]
        payload = [
            {
                "id": n,
                "posted": f"{pending_info[k][1].isoformat()} ({pending_info[k][1].strftime('%A')})",
                "text": pending_info[k][0],
            }
            for n, k in enumerate(chunk)
        ]
        prompt = PROMPT.replace("__ITEMS__", json.dumps(payload, ensure_ascii=False))
        try:
            response, model_used = _generate(client, prompt, limiter)
            requests_made += 1
            models_used.add(model_used)
        except LimitReached as exc:
            problem = f"AI paused ({str(exc)[:300]}) - remaining tasks will be checked on a later sync."
            break
        except AllModelsFailed as exc:
            problem = f"Every AI model failed ({str(exc)[:400]}) - tasks stay on their posted date and will be retried on the next sync."
            break
        except Exception as exc:  # noqa: BLE001
            code = _error_code(exc)
            problem = f"AI request failed{f' (HTTP {code})' if code else ''}: {str(exc)[:300]}"
            break

        parsed = _parse_response(getattr(response, "text", None))
        if parsed is None:
            problem = "AI answered in an unreadable format - nothing was changed."
            break
        for n, k in enumerate(chunk):
            if n not in parsed:
                continue  # model skipped it; don't cache, ask again next time
            posted = pending_info[k][1]
            d = _validated(parsed[n][0], parsed[n][1], posted)
            cache[k] = d.isoformat() if d else None
            for idx in pending[k]:
                results[idx] = d
            if d:
                found += 1
        _save_cache(cache_file, cache)

    asked = sum(len(pending[k]) for k in keys)
    note = f"AI checked {len(keys)} new task(s) in {requests_made} request(s) using {", ".join(sorted(models_used)) or "no model"}, found {found} deadline(s)"
    if cached_hits:
        note += f" ({cached_hits} answered from cache)"
    note += "."
    if problem:
        note += " " + problem
    return results, note
