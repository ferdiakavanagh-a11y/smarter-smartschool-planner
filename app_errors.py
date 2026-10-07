"""Turns low-level exceptions into short, friendly messages for the app.

`explain(exc)` returns a dict with: kind, title, message, hint, details.
kinds: login | config | network | server | unknown
"""

from __future__ import annotations

import traceback

try:  # requests is always installed (smartschool depends on it)
    import requests
except Exception:  # noqa: BLE001
    requests = None  # type: ignore[assignment]

# What to tell the user to do next, per kind
ADDRESS_NOT_FOUND_TITLE = "School address not found"
ADDRESS_HINT = (
    "Check the school address under Change login details. It should look like "
    "yourschool.smartschool.be, without https:// or slashes."
)

LOGIN_HINT = (
    "Check your details, then press Retry. Don't keep retrying with a wrong "
    "password - Smartschool can temporarily lock the account."
)


class SyncError(Exception):
    """A problem we already understand well enough to explain to the user."""

    def __init__(self, kind: str, title: str, message: str, hint: str = "", details: str = ""):
        super().__init__(message)
        self.kind, self.title, self.message, self.hint, self.details = kind, title, message, hint, details


def _chain(exc: BaseException):
    seen = set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc))
        yield exc
        exc = exc.__cause__ or exc.__context__


def address_problem(main_url: str, details: str = "") -> dict | None:
    """Friendly error if the school address is clearly malformed, else None."""
    u = (main_url or "").strip()
    if u and (u.lower().startswith(("http://", "https://")) or " " in u or "/" in u):
        return {"kind": "config", "title": "School address looks wrong",
                "message": f"The school address \"{u}\" isn't in the right format.",
                "hint": "Use just the address, without https:// or any slashes or spaces, for example "
                        "yourschool.smartschool.be. Fix it under Change login details.",
                "details": details}
    return None


def explain(exc: BaseException, main_url: str = "") -> dict:
    """Friendly description of any exception raised during a sync."""
    details = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

    for e in _chain(exc):
        if isinstance(e, SyncError):
            return {"kind": e.kind, "title": e.title, "message": e.message, "hint": e.hint,
                    "details": e.details or details}

    where = f" ({main_url})" if main_url else ""

    if requests is not None:
        for e in _chain(exc):
            if isinstance(e, requests.exceptions.SSLError):
                return {"kind": "network", "title": "Secure connection failed",
                        "message": f"Couldn't make a secure connection to Smartschool{where}.",
                        "hint": "Check that your computer's date and time are correct, and that no VPN, proxy "
                                "or security program is interfering. Then press Retry.",
                        "details": details}
            if isinstance(e, (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.InvalidURL)):
                bad = address_problem(main_url, details)
                if bad:
                    return bad
            if isinstance(e, requests.exceptions.TooManyRedirects):
                return {"kind": "config", "title": ADDRESS_NOT_FOUND_TITLE,
                        "message": f"Smartschool{where} kept redirecting without ever loading a page.",
                        "hint": ADDRESS_HINT, "details": details}
            if isinstance(e, requests.exceptions.InvalidURL):
                return {"kind": "config", "title": "School address looks wrong",
                        "message": "The school address in your login details isn't valid.",
                        "hint": "Fix it under Change login details (for example yourschool.smartschool.be).",
                        "details": details}
            if isinstance(e, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
                return {"kind": "network", "title": "Can't reach Smartschool",
                        "message": f"Couldn't connect to Smartschool{where}.",
                        "hint": "Check your internet connection and that the school address in your login "
                                "details is right (for example yourschool.smartschool.be). Then press Retry.",
                        "details": details}
            if isinstance(e, requests.exceptions.HTTPError):
                code = getattr(getattr(e, "response", None), "status_code", None)
                if code and code >= 500:
                    return {"kind": "server", "title": "Smartschool has a problem",
                            "message": f"Smartschool answered with an error (HTTP {code}).",
                            "hint": "This is on their side. Wait a few minutes and press Retry.",
                            "details": details}
                if code in (401, 403):
                    return {"kind": "login", "title": "Smartschool refused the login",
                            "message": "Smartschool didn't let this account in.", "hint": LOGIN_HINT,
                            "details": details}

    for e in _chain(exc):
        name = type(e).__name__
        text = str(e)
        if name in ("SmartSchoolDownloadError", "SmartSchoolJsonError") and getattr(e, "status_code", None):
            code = e.status_code
            if code == 404:
                return {"kind": "config", "title": ADDRESS_NOT_FOUND_TITLE,
                        "message": f"Smartschool answered \"page not found\" (HTTP 404){where}. "
                                   "That usually means the school address is wrong.",
                        "hint": ADDRESS_HINT, "details": details}
            if code >= 500:
                return {"kind": "server", "title": "Smartschool has a problem",
                        "message": f"Smartschool answered with an error (HTTP {code}).",
                        "hint": "This is on their side. Wait a few minutes and press Retry.",
                        "details": details}
            if code in (401, 403):
                return {"kind": "login", "title": "Smartschool refused the login",
                        "message": "Smartschool didn't let this account in.", "hint": LOGIN_HINT,
                        "details": details}
            if code != 200:
                return {"kind": "config", "title": "Unexpected answer from Smartschool",
                        "message": f"Smartschool answered with HTTP {code}{where}.",
                        "hint": ADDRESS_HINT + " If it is right, wait a few minutes and press Retry.",
                        "details": details}

    for e in _chain(exc):
        name = type(e).__name__
        text = str(e)
        if name == "SmartSchoolAuthenticationError":
            if "pyotp" in text:
                return {"kind": "config", "title": "2FA component missing",
                        "message": "Your account uses an authenticator app, but the 2FA component isn't available.",
                        "hint": "Reinstall the latest version of the app.", "details": details}
            if "Max login attempts" in text:
                return {"kind": "login", "title": "Login failed",
                        "message": "Smartschool kept sending back the login page, so the login wasn't accepted.",
                        "hint": LOGIN_HINT + " If your school address is right, check it too.",
                        "details": details}
            return {"kind": "login", "title": "Login failed",
                    "message": "Smartschool didn't accept the login.", "hint": LOGIN_HINT, "details": details}
        if name == "SmartSchoolJsonError" and "decode" in text.lower():
            # Smartschool answered with a web page (usually its login page) instead of data
            return {"kind": "login", "title": "Login failed",
                    "message": "Smartschool didn't accept the login.",
                    "hint": LOGIN_HINT + " If your details are right, Smartschool may be having a problem.",
                    "details": details}
        if isinstance(e, RuntimeError) and "verify and correct these attributes" in text:
            return {"kind": "config", "title": "Login details incomplete",
                    "message": f"Some required login details are empty: {text.split(':', 1)[-1].strip()}.",
                    "hint": "Open Change login details and fill them in.", "details": details}
        if isinstance(e, ValueError) and "authenticated user" in text:
            return {"kind": "login", "title": "Login failed",
                    "message": "Smartschool didn't accept the login.", "hint": LOGIN_HINT, "details": details}
        if name in ("YAMLError", "ScannerError", "ParserError") or isinstance(e, FileNotFoundError):
            return {"kind": "config", "title": "Login details unreadable",
                    "message": "The saved login details file is missing or damaged.",
                    "hint": "Open Change login details and enter them again.", "details": details}

    first = (str(exc).strip().splitlines() or [type(exc).__name__])[0][:300]
    return {"kind": "unknown", "title": "Something went wrong",
            "message": first or type(exc).__name__,
            "hint": "Press Retry. If it keeps happening, open Technical details below and report it.",
            "details": details}


# ---------------------------------------------------------------------------------------------
# Gemini (deadline detection) problems. These never stop a sync; they show as a banner instead.
# ---------------------------------------------------------------------------------------------

_AI_TEXT = {
    "key": (
        "Gemini key not working",
        "Google rejected your Gemini API key, so deadlines written inside assignment text couldn't be detected.",
        "Check the key under Change login details, or clear it to switch this feature off.",
        True,
    ),
    "limit": (
        "Gemini limit reached",
        "The free Gemini limit has been reached for now. Some tasks keep the date they were posted.",
        "They're checked again on a later sync.",
        False,
    ),
    "unavailable": (
        "Gemini unavailable",
        "Google's Gemini service didn't answer (it's busy, or there's no connection). Tasks keep their posted date.",
        "Try syncing again in a few minutes.",
        False,
    ),
    "format": (
        "Gemini answered unclearly",
        "Gemini sent back an answer the app couldn't read, so nothing was changed.",
        "Try syncing again. If it keeps happening, the deadlines still show their posted date.",
        False,
    ),
    "other": (
        "Gemini couldn't be used",
        "Deadline detection with Gemini failed, so tasks keep the date they were posted.",
        "Try syncing again later.",
        False,
    ),
}


def gemini_warning(kind: str, detail: str = "") -> dict:
    """Banner info for a Gemini problem: {source, kind, title, message, hint, fix, details}."""
    title, message, hint, fix = _AI_TEXT.get(kind, _AI_TEXT["other"])
    return {
        "source": "gemini",
        "kind": kind if kind in _AI_TEXT else "other",
        "title": title,
        "message": message,
        "hint": hint,
        "fix": fix,  # True -> banner offers "Change login details"
        "details": (detail or "")[:600],
    }


def read_main_url(creds_path) -> str:
    """School address from credentials.yml, for error messages. Never raises."""
    try:
        import yaml  # noqa: PLC0415

        with open(creds_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return str(data.get("main_url") or "")
    except Exception:  # noqa: BLE001
        return ""
