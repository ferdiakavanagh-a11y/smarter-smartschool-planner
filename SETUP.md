# Setup (Windows)

## 1. Install Python
Get Python 3.11+ from python.org if you don't have it. During install, tick
"Add python.exe to PATH".

## 2. Get the project files
Put this whole folder somewhere permanent, e.g. `C:\Users\<you>\smartschool-planner`.

## 3. Install dependencies
Open a terminal (cmd or PowerShell) in the folder and run:

```
pip install -r requirements.txt
```

This installs the Smartschool library and `pywebview` (which the real
desktop app uses for its window).

## 4. Add your credentials
Copy `credentials.yml.example` to `credentials.yml` in the same folder, and fill in:
- `username` / `password` - your normal Smartschool login
- `main_url` - your school's Smartschool address, WITHOUT `https://`
  (e.g. `yourschool.smartschool.be`)
- `mfa` - only relevant if login asks a security question or you have real
  2FA; see the comments in the file itself, and `debug_verification_question.py`
  if you're not sure what to put here.
- `gemini_api_key` - optional. Leave blank to skip. If set, it's used as a
  fallback for deadline text the built-in parser can't confidently figure
  out on its own - get a free key at https://aistudio.google.com/apikey.

`credentials.yml` stays local on your machine only - never share it or upload it anywhere.

## 5. Run the app
```
python desktop_app.py
```
A window opens: your planner, with four tabs (To-Do, Missed, Schedule, All
Classes), checkboxes you can tick off, and links out to Smartschool. First
run will take a few seconds while it logs in and syncs.

If login fails, most likely cause is `main_url` being wrong, or the security
question described above - `debug_verification_question.py` helps diagnose
that safely without guessing.

**Want an actual double-clickable app** (no typing `python desktop_app.py`
every time)? See [BUILD_EXE.md](BUILD_EXE.md) to build `SmartschoolPlanner.exe`.

## 6. (Optional) Automate a background sync every morning
The desktop app already syncs fresh data every time you open it, so this
step is optional - useful if you want the data ready and up to date
*before* you even open the app, via Windows Task Scheduler:

1. Open **Task Scheduler** (search it in the Start menu).
2. **Action -> Create Task...**
3. **General tab:** name it e.g. "Smartschool Planner Sync". Tick "Run whether user
   is logged on or not" if you want it to run even when you're not logged in.
4. **Triggers tab -> New:** Daily, set your preferred morning time (e.g. 07:00).
5. **Actions tab -> New:**
   - Action: "Start a program"
   - Program/script: full path to `run_daily.bat` (e.g.
     `C:\Users\<you>\smartschool-planner\run_daily.bat`)
6. Save. You'll be asked for your Windows password if you chose "run whether logged
   on or not".

This runs quietly in the background (no window pops up) and just refreshes
`data/planner_data.json`. Next time you open the app (or the exe), it shows
that data instantly, then syncs again anyway to catch anything newer.

## Notes / next steps
- Default window is 10 days back / 21 days ahead. Change with
  `python sync.py --days-back 14 --days-ahead 30` if running the CLI sync
  directly, or edit the numbers in `run_daily.bat` / `desktop_app.py`.
- `python build_dashboard.py` still works too, producing a plain
  `dashboard.html` you can open in any browser - same look as the app, but
  read-only (no persistent checkboxes), for whenever you don't want to run
  the Python app itself.
