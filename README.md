# Smartschool Planner

A real desktop app (not a browser tab, not a terminal) that pulls your
Smartschool planner data, figures out the *real* due date even when it's only
mentioned in an assignment's text rather than the day it was posted, and
shows it as an interactive, checkable planner with links back to Smartschool.

**Start here: [SETUP.md](SETUP.md)** for install steps.
**Want it as a double-clickable .exe?** See [BUILD_EXE.md](BUILD_EXE.md).

## What it does
- Logs into Smartschool (via the unofficial `smartschool` Python library)
  and pulls your planner cards from ~10 days back to ~21 days ahead
  (`--days-back` / `--days-ahead` to change that).
- Fetches each assignment's actual body text ("Info voor de leerling") -
  the planner's list endpoint only ever returns a title, never the body, so
  `planner_details.py` asks Smartschool's per-task endpoint separately for
  the real content (the route isn't documented, so it tries a short list of
  likely URLs once and remembers whichever one works).
- Figures out the real deadline from that text - e.g. "De deadline voor deze
  opdracht is VRIJDAG 25 SEPTEMBER", "date limite : 5/10", "DEADLINE 05/10" -
  instead of just using the day it was posted:
  - A free built-in keyword parser (`dutch_dates.py`, Dutch/French/German/
    English) exists but is **switched off by default** - see
    `USE_REGEX_DEADLINE_PARSER` in `sync.py`.
  - When a `gemini_api_key` is set in `credentials.yml`, every task that
    still needs a date is sent to Google's Gemini API - all bundled into
    **one request per sync** (not one call per task), answers are **cached**
    so unchanged tasks are never re-asked, and a **persistent rate limiter**
    keeps usage under Google AI Studio's free-tier limits for Flash models
    even across restarts. The model is explicitly told to answer "no
    deadline found" rather than guess, and any answer that isn't
    unambiguously *after* the posted date is discarded automatically.
  - Every AI-found date is clearly badged "AI-detected - verify" everywhere
    it appears, since it's the one part of this pipeline that isn't fully
    deterministic.
- Shows everything in a windowed app with four tabs:
  - **To-Do** - upcoming tasks, grouped Today / Tomorrow / This week / Later,
    with a course filter. Check items off; it's remembered next time.
  - **Missed** - overdue tasks, but only from the last 7 days (older ones
    are hidden as likely redundant).
  - **Schedule** - your day-by-day timetable, with each lesson's full
    assignment text and its own checkbox.
  - **All Classes** - literally every class period per day, even ones with
    no assignment attached - the closest thing to a full plain timetable.
    (This one is best-effort/experimental - see Known limitations below.)
- Click any task or lesson card to see everything captured about it in a
  detail view, including every raw field Smartschool sent back. Cards link
  out to the specific task in Smartschool in your browser.

## Files
| File | Purpose |
|---|---|
| `desktop_app.py` | **The real app** - run this (or build the exe from it) |
| `sync.py` | Fetches data from Smartschool, orchestrates due-date resolution |
| `planner_details.py` | Fetches each task's real body text (title-only otherwise) |
| `dutch_dates.py` | The free keyword deadline parser (off by default) |
| `gemini_dates.py` | Batched AI deadline detection, with caching + rate limiting |
| `planner_html.py` | The shared UI (used by both the app and the plain dashboard) |
| `task_state.py` | Remembers which tasks you've checked off |
| `build_dashboard.py` | No-install fallback: plain `dashboard.html`, read-only |
| `run_daily.bat` | Background sync only (no window), for Task Scheduler |
| `build_exe.bat` | Builds `SmartschoolPlanner.exe` (run once, see BUILD_EXE.md) |
| `credentials.yml.example` | Template - copy to `credentials.yml` and fill in |
| `debug_verification_question.py` | One-off helper if login asks a security question |
| `data/planner_data.json` | Raw structured output (created after first sync) |
| `data/completed_tasks.json` | Your checked-off tasks |
| `data/gemini_cache.json` | Cached AI answers (skips re-asking about unchanged tasks) |
| `data/gemini_usage.json` | Rate-limit bookkeeping, so limits hold across restarts |
| `data/planner_detail_route.json` | Which detail-endpoint guess worked, once found |

## Switching the free parser back on
`dutch_dates.py` still works and is still tested - it's just not in the
pipeline right now, since the AI pass (working off real body text) handles
the same job with much better recall. To use it as a free first pass before
AI is asked (or instead of AI, if you don't set a `gemini_api_key`), open
`sync.py` and set:
```python
USE_REGEX_DEADLINE_PARSER = True
```

## Known limitations
- **The detail-endpoint route is a guess.** `planner_details.py` tries a
  short list of plausible URLs once per install and remembers whichever one
  works (see `data/planner_detail_route.json` and `data/detail_probe.log` if
  none of them do). If your school's route isn't in that list, tasks fall
  back to title-only text, and deadline detection will miss anything that
  isn't in the title. You can also hand it the exact route yourself via
  `planner_detail_url` in `credentials.yml` if you find it.
- **All Classes tab**: getting a *plain* timetable (classes with nothing
  assigned at all) means asking the planner endpoint for more than it's
  documented to give back - unverified against a live account. If it comes
  up empty even though you have plain classes with no homework, tell me and
  I'll adjust the guess.
- **"Open in Smartschool" links** are reconstructed from one real example
  URL - if a link 404s or lands on the wrong item, the segment order/suffix
  may need adjusting; tell me what you see.
- A separate legacy "future tasks" endpoint some schools expose returns a
  401 for at least one account tested - fails gracefully, doesn't affect
  to-dos or deadlines from the main planner data.
- **AI-detected due dates** aren't fully deterministic. Every safeguard that
  can be automated is (batching, caching, rate limits, confidence gating,
  rejecting implausible dates) but the "AI-detected - verify" badge is there
  for a reason - worth a glance before trusting one blindly.


## License

This project is licensed under the [GNU General Public License v3.0](LICENSE) — see the LICENSE file for details. 

This project incorporates the `smartschool` library, which is also licensed under the GNU General Public License v3.0.

## Disclaimer

This project is an unofficial, community-developed application and is not affiliated with, maintained, or endorsed by Smartschool or its parent companies. Use of this software is subject to the warranty disclaimers outlined in the GPLv3 license.


## Third-Party Assets & Credits

- **Window Control Buttons**: Visual style derived from [hyper-mac-controls](https://github.com/krve/hyper-mac-controls) by **krve** ([MIT License](https://github.com/krve/hyper-mac-controls/blob/master/LICENSE)).
