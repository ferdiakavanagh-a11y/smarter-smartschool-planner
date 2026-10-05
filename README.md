# Smartschool Planner

A real desktop app (not a browser tab, not a terminal) that pulls your
Smartschool planner data, figures out the *real* due date even when it's only
mentioned in an assignment's text rather than the day it was posted, and
shows it as an interactive, checkable planner with links back to Smartschool.

# code signing policy

   Free code signing provided by [SignPath.io](https://signpath.io), certificate by [SignPath Foundation](https://signpath.org) (pending). See the [code signing policy](CODE_SIGNING_POLICY.md).

## Install (easiest)

1. Go to the **[Releases](../../releases)** page and download `SmartschoolPlanner-Setup.exe`.
2. Open it. On the login page, enter your Smartschool details.
3. Wait for it to finish, then open **Smartschool Planner** from the Start Menu.

That's all. No Python, no files to edit. Your login details are saved **only on
your own computer** and are removed again if you uninstall. Windows SmartScreen
may warn about an unsigned app - click **More info**, then **Run anyway**.

To change your login details later, use **Smartschool Planner - Change login
details** in the Start Menu.

Prefer running from source? See **[SETUP.md](SETUP.md)**. Want to build the exe
yourself? See **[BUILD_EXE.md](BUILD_EXE.md)**, or double-click
`setup_and_build.bat` to install the dependencies, build the exe and (with
[Inno Setup 6](https://jrsoftware.org/isdl.php) installed) the installer.

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
  - When a `gemini_api_key` is set, every task that still needs a date is sent
    to Google's Gemini API - all bundled into **one request per sync** (not
    one call per task), answers are **cached** so unchanged tasks are never
    re-asked, and a **persistent rate limiter** keeps usage under the free-tier
    limits even across restarts. The model is explicitly told to answer "no
    deadline found" rather than guess, and any answer that isn't unambiguously
    *after* the posted date (or is implausibly far away) is discarded.
  - Every AI-found date is clearly badged "AI-detected - verify" everywhere
    it appears, since it's the one part of this pipeline that isn't fully
    deterministic.

## The app

Five tabs:
- **To-Do** - upcoming tasks, grouped Today / Tomorrow / This week / Later,
  with a course filter. Check items off; it's remembered next time.
- **Missed** - overdue tasks, but only from the last 7 days (older ones
  are hidden as likely redundant), with a badge showing how many.
- **Schedule** - your day-by-day timetable, with each lesson's full
  assignment text and its own checkbox.
- **All Classes** - literally every class period per day, even ones with
  no assignment attached - the closest thing to a full plain timetable.
  (Best-effort/experimental - see Known limitations below.)
- **Grades** - your results, newest first: score, maximum, percentage, course,
  date, teacher, any feedback, and whether it counts towards your average.

Click any task, lesson or grade to see everything captured about it in a
detail view. Cards link out to the specific task in Smartschool in your browser.

## New in V2
- **Grades tab** - pulls your evaluations from Smartschool and shows them in
  the app. If grades can't be fetched, the rest of the planner still works and
  the tab says why.
- **Search** - one search box across tasks, notes, lessons and grades.
- **Pin to top** - pin any task from its detail view; pinned tasks get their
  own **Pinned** section at the top of the To-Do list.
- **Private notes** - add your own notes to any task. They're saved on your
  computer only, and they're searchable.
- **Display settings** - choose the **Vivid** or **Frost** look, adjust the
  glass effect with a slider, and switch on **Reduce motion**. Settings are
  remembered.
- **Native-feeling window** - a frameless window with its own minimise /
  maximise / close buttons and drag-to-resize. Maximising stays inside the
  taskbar, and Windows 11 rounded corners are used where available.
- **Smarter AI deadline detection** - falls back through a list of Gemini
  models if one is overloaded or out of quota, tracks each model's own free-tier
  limits, and skips tasks with nothing date-like in them to save quota.
- **Safer links** - only `http` / `https` links can be opened from the app.
- **More 2FA support** - authenticator-app (TOTP) secrets work in the installed
  app, as well as the birthdate security question.
- **One-click installer** - download one file, fill in your login, done (see
  the top of this page). Birthdates are checked and converted to the required
  `YYYY-MM-DD` format as you type them in.
- **First-run setup window** - if `credentials.yml` is missing, the app asks
  for your details and creates it for you.
- **First sync** - right after you save your details for the first
  time, at the top right you have to click the sync button once so you don't start on an empty screen.

## Files
| File | Purpose |
|---|---|
| `desktop_app.py` | **The real app** - run this (or build the exe from it) |
| `setup_ui.py` | First-run / "change login details" window; writes `credentials.yml` |
| `sync.py` | Fetches planner data and grades, orchestrates due-date resolution |
| `planner_details.py` | Fetches each task's real body text (title-only otherwise) |
| `dutch_dates.py` | The free keyword deadline parser (off by default) |
| `gemini_dates.py` | Batched AI deadline detection, with caching, fallback and rate limiting |
| `planner_html.py` | The shared UI (used by both the app and the plain dashboard) |
| `task_state.py` | Remembers checked-off tasks, pins, notes and display settings |
| `build_dashboard.py` | No-install fallback: plain `dashboard.html`, read-only |
| `run_daily.bat` | Background sync only (no window), for Task Scheduler |
| `build_exe.bat` | Builds `SmartschoolPlanner.exe` (see BUILD_EXE.md) |
| `setup_and_build.bat` | One click: install dependencies, build the exe, then the installer |
| `SmartschoolPlanner.iss` | Inno Setup script for the installer |
| `.github/workflows/release.yml` | Builds the installer on GitHub and attaches it to a release |
| `credentials.yml.example` | Template - copy to `credentials.yml` and fill in (not needed with the installer) |
| `data/planner_data.json` | Raw structured output (created after first sync) |
| `data/completed_tasks.json` | Your checked-off tasks |
| `data/pinned_tasks.json` | Your pinned tasks |
| `data/task_notes.json` | Your private notes |
| `data/ui_settings.json` | Your display settings |
| `data/gemini_cache.json` | Cached AI answers (skips re-asking about unchanged tasks) |
| `data/gemini_usage.json` | Rate-limit bookkeeping, so limits hold across restarts |
| `data/planner_detail_route.json` | Which detail-endpoint guess worked, once found |

## Privacy
`credentials.yml` and everything in `data/` stay on your computer. They are
never uploaded anywhere, and the installer never contains anyone's login. Your
details are only sent where the app needs them: your username and password go
to Smartschool to log in, and, if you set a Gemini key, assignment text goes to
Google for deadline detection. Treat the Gemini key like a password.

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
  documented to give back - unverified against a live account.
- **"Open in Smartschool" links** are reconstructed from one real example
  URL - if a link 404s or lands on the wrong item, the segment order/suffix
  may need adjusting.
- A separate legacy "future tasks" endpoint some schools expose returns a
  401 for at least one account tested - fails gracefully, doesn't affect
  to-dos or deadlines from the main planner data.
- **AI-detected due dates** aren't fully deterministic. Every safeguard that
  can be automated is (batching, caching, rate limits, confidence gating,
  rejecting implausible dates) but the "AI-detected - verify" badge is there
  for a reason - worth a glance before trusting one blindly.
- **The installer is unsigned**, so Windows SmartScreen shows a warning the
  first time.


## License

This project is licensed under the [GNU General Public License v3.0](LICENSE) — see the LICENSE file for details. 

This project incorporates the `smartschool` library, which is also licensed under the GNU General Public License v3.0.

## Disclaimer

This project is an unofficial, community-developed application and is not affiliated with, maintained, or endorsed by Smartschool or its parent companies. Use of this software is subject to the warranty disclaimers outlined in the GPLv3 license.


## Third-Party Assets & Credits

- **Window Control Buttons**: Visual style derived from [hyper-mac-controls](https://github.com/krve/hyper-mac-controls) by **krve** ([MIT License](https://github.com/krve/hyper-mac-controls/blob/master/LICENSE)).


test