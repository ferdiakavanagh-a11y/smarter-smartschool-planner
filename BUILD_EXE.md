# Turning this into a real desktop app (Windows .exe)

This can't be built for you remotely - an .exe has to be built on the same
kind of machine it'll run on. But it's a one-time, one-command step on your
end, and after that you get a real windowed app: no terminal, no typing
commands, just double-click and it opens.

## One-time build

1. Make sure you've already run `pip install -r requirements.txt` (see
   SETUP.md) - this now also installs `pywebview`, which is what gives the
   app its actual window (no browser, no console).
2. **If you built an exe from this project before** (whether the old
   console version or an earlier version of the windowed app): delete
   `SmartschoolPlanner.spec`, and the `build\` and `dist\` folders if they
   exist, first. The build script reuses that `.spec` file to speed up
   rebuilds, but a stale one won't include newly-added dependencies (like
   `pywebview` originally, or `google-genai` for the optional AI deadline
   fallback) - it would silently rebuild an outdated version.
3. Double-click **build_exe.bat** in this folder (or run it from a
   terminal). It installs PyInstaller and packages `desktop_app.py` + its
   dependencies into `SmartschoolPlanner.exe`, then copies that exe into
   this same folder.
4. This takes a minute or two. When it's done you'll have
   `SmartschoolPlanner.exe` sitting next to `sync.py`, `credentials.yml`, etc.

You can delete the `build\` and `dist\` folders and the `.spec` file
afterwards - they're just leftovers from the build, not needed to run the
exe.

## Using it

Double-click `SmartschoolPlanner.exe`. A real window opens (no console, no
browser chrome) showing:
- Whatever data you already have, instantly (if you've synced before)
- Then it syncs fresh in the background and updates automatically
- A "Sync now" button in the top-right to refresh on demand
- Four tabs: **To-Do**, **Missed**, **Schedule**, **All Classes** (see
  README.md for what each shows)

If something goes wrong (bad credentials, no internet), the window shows the
error directly with a **Retry** button - no console output to dig through.

`credentials.yml` still needs to sit next to the exe, same as before - it's
not baked into the exe (on purpose, so you never need to rebuild it just
because you changed a password).

## One dependency to be aware of

Under the hood, this uses Microsoft's WebView2 to render the window on
Windows. Windows 10/11 machines almost always already have this (Microsoft
ships it via Windows Update), so most people won't notice anything. If the
app fails to open with a WebView2-related error, install it from
Microsoft directly: search "WebView2 Runtime" or go to
https://developer.microsoft.com/microsoft-edge/webview2/ and get the
"Evergreen Bootstrapper".

## Automating it

`run_daily.bat` (for Task Scheduler) still just runs `sync.py` +
`build_dashboard.py` in the background - no window pops up, which is exactly
what you want for an unattended scheduled task. The next time you open
`SmartschoolPlanner.exe` yourself, it'll show that freshly-synced data
immediately and then sync again in the background to catch anything newer.

## Rebuilding after changes

Any time `desktop_app.py`, `sync.py`, `build_dashboard.py`, `planner_html.py`,
`task_state.py`, or `dutch_dates.py` changes (e.g. I send you an update),
just double-click `build_exe.bat` again to rebuild the exe with the new code.

## If the build or the app fails

Most common cause: PyInstaller couldn't find something the `smartschool` or
`pywebview` libraries need at runtime (they're discovered automatically by
scanning imports, and occasionally something written in an unusual way gets
missed - `pywebview`'s Windows backend in particular relies on `pythonnet`,
which PyInstaller can be picky about). If the resulting .exe crashes right
away with an import error, paste me the error - it's almost always fixed by
adding one more `--hidden-import=...` or `--collect-all ...` flag to
`build_exe.bat`. I can't fully test this build target without a Windows
machine, so the first build is the real test - expect we might need one
round of fixes based on what actually happens on your machine.
