# Building the Windows desktop app

## Build

1. Install Python 3.12. The build installs `requirements-release.txt`, including pinned runtime and PyInstaller versions.
2. Run **build_exe.bat**, or **setup_and_build.bat** to also compile the installer
   when Inno Setup 6 is installed.
3. The build produces `dist\SmartschoolPlanner\SmartschoolPlanner.exe` and its
   `_internal` support directory. It also copies both beside the source files,
   keeping your existing local credentials and planner data in use.

The executable uses PyInstaller's folder bundle so libraries do not have to be
extracted on every launch. **Keep `_internal` beside the executable.** To move a
portable copy, copy the complete bundle, not just the EXE. Credentials and the
`data` directory remain beside the EXE, separate from `_internal`.

Builds always regenerate the spec from the current command; old single-file
specs are not reused. You can delete `build`, `dist`, and the generated `.spec`
after compiling the installer, but keep the root `_internal` to run the local EXE.

The release workflow checks dependency compatibility before building.
Tests are kept locally and excluded from Git. Update the dependency lock deliberately
when changing dependencies.

## Installer and updates

Inno Setup packages the complete `dist\SmartschoolPlanner` bundle. GitHub's
release workflow still publishes `SmartschoolPlanner-Setup.exe` and its checksum.
Existing shortcuts, install location, app identity, credentials, and data paths
are unchanged. The existing updater downloads and verifies the installer, which
replaces both the EXE and bundled support files. First-install and upgrade
rendering-choice behavior is unchanged. A separate hidden worker monitors the installer
exit code and reopens the app with an error message if installation fails.

## Using it

Double-click `SmartschoolPlanner.exe`. A real window opens (no console, no
browser chrome) showing:
- Whatever data you already have, instantly (if you've synced before)
- Opens the saved planner without syncing; updates are checked in the background
- A "Sync now" button in the top-right to refresh on demand
- Six tabs: **To-Do**, **Missed**, **Schedule**, **All Classes**, **Grades**, **LVS** (see
  README.md for what each shows)

If something goes wrong (bad credentials, no internet), the window shows the
error directly with a **Retry** button - no console output to dig through.

`credentials.yml` beside the exe stores nonsecret configuration and a vault
reference. Passwords and API keys live in Windows Credential Manager. Use the
app's login editor to change them; no rebuild is needed.

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
immediately. Use Sync now to fetch newer changes.

## Rebuilding after changes

Any time `desktop_app.py`, `sync.py`, `build_dashboard.py`, `planner_html.py`,
`task_state.py`, or `dutch_dates.py` changes (e.g. I send you an update),
just double-click `build_exe.bat` again to rebuild the exe with the new code.

## Release notes and update notices

When publishing a release, update both `__version__` and `RELEASE_NOTES` in
`version.py`, and write the complete feature list in the GitHub release body.
The updater saves those GitHub notes locally before launching the installer.
Bundled notes provide an offline fallback, including upgrades from older apps.

The installer marks upgrades with `--updated`; fresh installs do not show an
update notice. Both the update offer and What's new use the planner's existing
glass sheet and themes. Dismissed versions are remembered in the local
`data/update_notice.json` file. No planner or credential data is included.

## If the build or the app fails

Most common cause: PyInstaller couldn't find something the `smartschool` or
`pywebview` libraries need at runtime (they're discovered automatically by
scanning imports, and occasionally something written in an unusual way gets
missed - `pywebview`'s Windows backend in particular relies on `pythonnet`,
which PyInstaller can be picky about). If the resulting .exe crashes right
away with an import error, paste me the error - it's almost always fixed by
adding one more `--hidden-import=...` or `--collect-all ...` flag to
`build_exe.bat`. Run your local checks and test the built
installer on a separate Windows account before publishing it.
