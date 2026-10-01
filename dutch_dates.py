"""
claude generated fallback for if the ai fails or you need to verify deadlines without internet.
"""

from __future__ import annotations

import re
from datetime import date, timedelta

DUTCH_WEEKDAYS = {
    "maandag": 0,
    "dinsdag": 1,
    "woensdag": 2,
    "donderdag": 3,
    "vrijdag": 4,
    "zaterdag": 5,
    "zondag": 6,
    # English
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
    # French
    "lundi": 0,
    "mardi": 1,
    "mercredi": 2,
    "jeudi": 3,
    "vendredi": 4,
    "samedi": 5,
    "dimanche": 6,
    # German
    "montag": 0,
    "dienstag": 1,
    "mittwoch": 2,
    "donnerstag": 3,
    "freitag": 4,
    "samstag": 5,
    "sonntag": 6,
}

DUTCH_MONTHS = {
    "januari": 1,
    "februari": 2,
    "maart": 3,
    "april": 4,
    "mei": 5,
    "juni": 6,
    "juli": 7,
    "augustus": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "december": 12,
    # English (months already covered above are spelled the same or handled by
    # the Dutch entry - only the genuinely different English spellings are added)
    "january": 1,
    "february": 2,
    "march": 3,
    "june": 6,
    "july": 7,
    "october": 10,
    # French
    "janvier": 1,
    "février": 2,
    "mars": 3,
    "avril": 4,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
    # German (only spellings not already covered above)
    "januar": 1,
    "februar": 2,
    "märz": 3,
    "dezember": 12,
}

# Words that signal "there's a deadline nearby in this text", not just an
# incidental date mention. Deliberately NOT matching a bare "op" or "voor" -
# too common in Dutch and would false-positive on things like "besproken op
# donderdag vorige week". Test/toets dates get their own narrower phrase
# instead ("toets op ...", "test op ...").
#
# This school also teaches in French/German/English, and those subjects'
# assignment titles are often written in that language too - so the signal
# phrases cover common deadline wording in all four. Real examples this list
# is built against include things like:
#   "De deadline voor deze opdracht is VRIJDAG 25 SEPTEMBER."
#   "Frans - ... (date limite : lundi 5/10)"
#   "English - ... (DEADLINE 05/10)"
SIGNAL_WORDS = re.compile(
    r"(tegen|ten\s+laatste(?:\s+op)?|deadline|uiterlijk(?:\s+(?:op|tegen))?|"
    r"in\s+te\s+dienen(?:\s+tegen|\s+op)?|"
    r"indienen(?:\s+tegen|\s+op)?|insturen(?:\s+tegen|\s+op)?|binnenbrengen(?:\s+tegen|\s+op)?|"
    r"af\s+te\s+geven(?:\s+tegen|\s+op)?|klaar\s+tegen|"
    r"moet\s+binnen\s+zijn(?:\s+(?:tegen|op))?|verwacht\s+(?:tegen|op)|"
    r"sluit(?:ingsdatum)?(?:\s+op)?|voor|"
    r"(?:toets|test|proefwerk|examen|SO|taak)\s+op|"
    # French
    r"date\s+limite|à\s+rendre(?:\s+(?:le|pour))?|remettre\s+(?:pour|le)|au\s+plus\s+tard(?:\s+le)?|"
    # German
    r"bis\s+zum|abzugeben|f[äa]llig(?:\s+am)?|sp[äa]testens(?:\s+am)?|abgabetermin\s*:?|"
    # English (avoid bare "due" alone - "due to" is a common non-deadline phrase)
    r"due\s*:|due\s+(?:by|on|date)|hand\s+in\s+by|submit\s+by|turn\s+in\s+by|complete\s+by)\b",
    re.IGNORECASE,
)

NUMERIC_DATE = re.compile(r"\b(\d{1,2})[/\-.](\d{1,2})(?:[/\-.](\d{2,4}))?\b")
MONTH_NAME_DATE = re.compile(
    r"\b(\d{1,2})\s+(" + "|".join(DUTCH_MONTHS.keys()) + r")\b", re.IGNORECASE
)
WEEKDAY_NAME = re.compile(r"\b(" + "|".join(DUTCH_WEEKDAYS.keys()) + r")\b", re.IGNORECASE)

# How far to look around a signal word for a date - both directions, since
# teachers write "deadline is FRIDAY 25/9" as often as "FRIDAY 25/9 is the
# deadline". Generous on purpose: a full sentence like "De deadline voor deze
# opdracht is VRIJDAG 25 SEPTEMBER" needs real room to find the date at the end.
WINDOW_CHARS = 80


def _next_weekday_on_or_after(ref: date, target_weekday: int) -> date:
    days_ahead = (target_weekday - ref.weekday()) % 7
    return ref + timedelta(days=days_ahead)


def _resolve_year(ref: date, month: int, day: int) -> date:
    """Pick the year closest to ref that doesn't put the date more than ~60 days in the past."""
    candidate = date(ref.year, month, day)
    if (ref - candidate).days > 60:
        candidate = date(ref.year + 1, month, day)
    return candidate


def _find_date_in_snippet(snippet: str, reference_date: date) -> date | None:
    m = NUMERIC_DATE.search(snippet)
    if m:
        day, month = int(m.group(1)), int(m.group(2))
        year_part = m.group(3)
        try:
            if year_part:
                year = int(year_part)
                if year < 100:
                    year += 2000
                return date(year, month, day)
            return _resolve_year(reference_date, month, day)
        except ValueError:
            pass  # fall through to other patterns

    m = MONTH_NAME_DATE.search(snippet)
    if m:
        day = int(m.group(1))
        month = DUTCH_MONTHS[m.group(2).lower()]
        try:
            return _resolve_year(reference_date, month, day)
        except ValueError:
            pass

    m = WEEKDAY_NAME.search(snippet)
    if m:
        return _next_weekday_on_or_after(reference_date, DUTCH_WEEKDAYS[m.group(1).lower()])

    return None


def extract_due_date(text: str | None, reference_date: date) -> tuple[date | None, bool]:
    """
    Returns (due_date, was_inferred_from_text).
    due_date is None if nothing was found (caller should fall back to reference_date).
    """
    if not text:
        return None, False

    for m in SIGNAL_WORDS.finditer(text):
        # Look both after AND before the signal word - teachers write both
        # "deadline is FRIDAY 25/9" and "FRIDAY 25/9 is the deadline".
        after = text[m.end() : m.end() + WINDOW_CHARS]
        found = _find_date_in_snippet(after, reference_date)
        if found:
            return found, True

        before_start = max(0, m.start() - WINDOW_CHARS)
        before = text[before_start : m.start()]
        found = _find_date_in_snippet(before, reference_date)
        if found:
            return found, True

    return None, False


def resolve_due_date(text: str | None, reference_date: date) -> tuple[date, bool]:
    """Convenience wrapper: always returns a usable date, falling back to reference_date."""
    found, inferred = extract_due_date(text, reference_date)
    return (found, True) if found else (reference_date, False)
