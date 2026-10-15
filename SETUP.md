# Setup (Windows)

## Easiest: the installer
Download `SmartschoolPlanner-Setup.exe` from the **Releases** page of the
repo, open it and wait for installation to finish. Enter your Smartschool
login in the app on its first launch. Then open **Smartschool Planner** from the Start Menu. No Python
and no files to edit - the rest of this page is only for running from source.

To change your login details later, use **Smartschool Planner - Change login
details** in the Start Menu.

---

## Running from source

### 1. Install Python
Get Python 3.12 or newer from python.org if you don't have it. During install, tick
"Add python.exe to PATH".

### 2. Get the project files
Put this whole folder somewhere permanent, e.g. `C:\Users\<you>\smartschool-planner`.

### 3. Install dependencies
Open a terminal (cmd or PowerShell) in the folder and run:

```
pip install -r requirements.txt
```

This installs the Smartschool library, `pywebview` (which the desktop app
uses for its window), the Gemini client and `pyotp` (only used if your account
uses an authenticator app for 2FA).

### 4. Add your credentials
The easy way: skip this step. The first time you run the app without a
`credentials.yml`, a setup window opens, asks for your details and creates the
file for you. You can reopen it any time with:

```
python desktop_app.py --setup
```

Secrets (username, password, security answer and optional Gemini key) are saved
in Windows Credential Manager, under your Windows account. `credentials.yml`
contains only the school address, advanced configuration and a vault reference.
Existing plaintext files are migrated automatically at startup or sync, after
verifying the vault entry. There is no plaintext storage fallback. The vault also binds
your password to the approved school hostname. Upgrading from an older vault format
requires confirming the school and re-entering the password once. Changing the hostname
in YAML cannot redirect a saved password.

Session cookies are encrypted with Windows DPAPI under your Windows account and
saved in `data/sessions/`. The old library cookies and user cache for the account are
removed. Malformed YAML can be repaired in the login editor; the original is kept
as an encrypted `credentials.recovery.bin` file.

Use Settings > Change login info to edit secrets. A Gemini key is optional;
without one, date checking uses Local. Moving the app folder, changing Windows
accounts or moving to a new computer requires entering your login again.
Task Scheduler must run under the Windows account that saved the credentials.
Windows Home is supported; other operating systems cannot save credentials.

### 5. Run the app
```
python desktop_app.py
```
A window opens: your planner, with six tabs (To-Do, Missed, Schedule, All
Classes, Grades, LVS), checkboxes you can tick off, search, pinning, private notes,
and links out to Smartschool.

The app never syncs on its own when you open it. It shows the last saved data
straight away when it belongs to the approved account. After changing accounts,
old data is hidden until that account syncs successfully. Click the sync button to log in and fetch fresh data (the very
first sync runs automatically right after you save your details in the setup
window). A sync takes a few seconds.

If login fails, the usual causes are a wrong username or password, `main_url`
being wrong (it must not start with `https://`), or the security answer
(a birthdate must be written as `YYYY-MM-DD`). Use Settings > Change login info
(or run `python desktop_app.py --setup`) and sync again. Don't retry many
times with a wrong password, as Smartschool can lock the account for a while.

**Want an actual double-clickable app** (no typing `python desktop_app.py`
every time)? See [BUILD_EXE.md](BUILD_EXE.md) to build `SmartschoolPlanner.exe`,
or double-click `setup_and_build.bat` to install the dependencies, build the
exe and (if [Inno Setup 6](https://jrsoftware.org/isdl.php) is installed) the
installer in one go.

### 6. (Optional) Automate a background sync every morning
The app only syncs when you press the sync button, so this step is useful if
you want the data ready and up to date *before* you even open the app, via
Windows Task Scheduler:

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
that data straight away.

`run_daily.bat` needs Python and works from the source folder. It doesn't
apply to the installed version.

## Performance on laptops
The Windows WebView2 renderer uses hardware acceleration by default. The app
does not disable it. Glass texture generation skips neutral interior pixels,
and unused refraction filters are evicted while filters still in use are kept.
Background wallpaper animations pause when the app loses focus.

To try updated source code, restart `python desktop_app.py`. A built or installed
`.exe` does not pick up Python source changes: rebuild it with `build_exe.bat`
or install a release containing the changes.

Performance with other browser tabs open depends on available RAM and GPU load.
Verify scrolling and opening Settings on the target laptop; texture-generation
benchmarks alone do not measure frame rate.

## Notes / next steps
- Default window is 10 days back / 21 days ahead. Change with
  `python sync.py --days-back 14 --days-ahead 30` if running the CLI sync
  directly, or edit the numbers in `run_daily.bat` / `desktop_app.py`.
- `python build_dashboard.py` still works too, producing a plain
  `dashboard.html` you can open in any browser - same look as the app, but
  read-only (no persistent checkboxes), for whenever you don't want to run
  the Python app itself.
