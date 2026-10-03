"""Finds a task's real deadline in free text ("tegen donderdag", "ten laatste op 30/09"), relative to the posting date.
Best-effort: misses fall back to the posted date; signal words limit false positives."""

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
    # English (only spellings not covered above)
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
    # German (new spellings only)
    "januar": 1,
    "februar": 2,
    "märz": 3,
    "dezember": 12,
}

# Phrases signalling a nearby deadline (Dutch/French/German/English).
# Bare "op"/"voor" are excluded as too common; tests use narrower phrases ("toets op ...").
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
    # English (not bare "due": "due to")
    r"due\s*:|due\s+(?:by|on|date)|hand\s+in\s+by|submit\s+by|turn\s+in\s+by|complete\s+by)\b",
    re.IGNORECASE,
)

NUMERIC_DATE = re.compile(r"\b(\d{1,2})[/\-.](\d{1,2})(?:[/\-.](\d{2,4}))?\b")
MONTH_NAME_DATE = re.compile(
    r"\b(\d{1,2})\s+(" + "|".join(DUTCH_MONTHS.keys()) + r")\b", re.IGNORECASE
)
WEEKDAY_NAME = re.compile(r"\b(" + "|".join(DUTCH_WEEKDAYS.keys()) + r")\b", re.IGNORECASE)

# search window around a signal word, both directions (word order varies)
WINDOW_CHARS = 80


def _next_weekday_on_or_after(ref: date, target_weekday: int) -> date:
    days_ahead = (target_weekday - ref.weekday()) % 7
    return ref + timedelta(days=days_ahead)


def _resolve_year(ref: date, month: int, day: int) -> date:
    """Year closest to ref, at most ~60 days in the past."""
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
            pass  # try other patterns

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
    """Returns (due_date, was_inferred); due_date is None if nothing found."""
    if not text:
        return None, False

    for m in SIGNAL_WORDS.finditer(text):
        # look before and after the signal word
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
    """Always returns a date; falls back to reference_date."""
    found, inferred = extract_due_date(text, reference_date)
    return (found, True) if found else (reference_date, False)
