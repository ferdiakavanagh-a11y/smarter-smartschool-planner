# Smarter Smartschool Planner

A Windows desktop app for your Smartschool timetable, assignments, results,
student follow-up (LVS), and messages. Choose **Liquid Glass** for translucent
controls and customizable backgrounds or **Smartschool** for compact top
navigation and solid panels. Both appearances support English and Dutch.

## Install on Windows

Download `SmartschoolPlanner-Setup.exe` from the
[GitHub Releases page](https://github.com/ferdiakavanagh-a11y/smarter-smartschool-planner/releases).
On first launch, sign in with your Smartschool account and choose an appearance.
The initial sync starts after setup.

On later launches, the app shows your last verified planner snapshot and refreshes
the inbox automatically. Use **Sync** to refresh planner data. In Smartschool mode,
the top-bar sync button refreshes the current folder while you are in **Messages**.

## Run from source

Use Python 3.12 on Windows:

```powershell
python -m pip install -r requirements.txt
python compile_shaders.py
python desktop_app.py
```

The source entry point and installed executable use the same Qt interface.
WebView2 and pythonnet are no longer required. See [setup](SETUP.md) and
[building the Windows executable](BUILD_EXE.md).

## Features

- **Tasks** — Filter by course, type or pin. Browse missed and completed work,
  undo completion changes, and keep private task notes.
- **Planner** — Browse the Smartschool week grid or lesson list. Open a lesson
  for its timetable information, linked assignments and available attachments.
  Access teacher replacements from any tab in Smartschool mode.
- **Results** — View published grades, feedback and weighted averages. Smartschool
  mode groups results by month and offers subject, school year and period filters.
- **LVS** — Browse notes and absences. The app fetches accessible note content
  in advance and tracks read status by account and school year.
- **Messages** — Read folders and open attachments, reply or forward, and save
  local rich-text drafts with lists, tables and links. Schedule a message if
  your school supports it. Draft a reply with Gemini using an optional API key.
- Compact Focus with a monotonic stopwatch, completion, pause and keep-on-top.
- Clear/Vivid and Auto/Light/Dark themes; independent frosting and distortion;
  four backgrounds; text sizing, reduced motion and high contrast. New installs default to Clear Light with Soft colours; saved preferences are retained.
- Login and local/Gemini date-checker settings. Gemini requires your own API key
  and sends relevant assignment text to Google's service during sync. Local
  checking works without that service.
- Background sync/setup/update work, visible errors and retry. Existing verified
  installer and release-notice mechanisms are retained.

Notes, pins and completion use the existing state files and task identifiers.
Edits are written before the displayed model changes. A failed note save keeps
the draft and vetoes closing the window. Account-mismatched cache data is not
displayed. Login secrets remain in the existing Windows credential storage.

## Source layout

| File | Responsibility |
| --- | --- |
| `desktop_app.py`, `qml_app/runtime.py` | Desktop launch and account helper modes |
| `qml_app/backend.py` | Queued service bridge, account checks, settings and updates |
| `qml_app/model.py`, `production_model.py`, `sections.py` | Task model and snapshot presentation |
| `qml_app/*.qml`, `Icons.js`, `shaders/` | Interface, artwork and optical shaders |
| `sync.py`, `planner_details.py` | Existing fetch, parsing and access rules |
| `task_state.py`, `credential_store.py`, `secure_session.py` | Durable state and account/session protection |
| `setup_ui.py`, `updater.py` | Protected login form and verified installer flow |

`qml_app/main.py` remains an isolated synthetic development harness. Production
launches through `desktop_app.py` and never selects synthetic fixtures.
The old HTML renderer, dashboard builder and WebView comparison scripts have
been removed. Existing snapshots and user-state files are retained.

## Packaging and licensing

Run `build_exe.bat` or `setup_and_build.bat`. The build compiles GLSL with the
matching pinned Qt version and bundles QML, icons and shader files. Development
environments and test data are excluded.

Adapted material techniques retain their MIT notices in
[third-party notices](qml_app/THIRD_PARTY_NOTICES.md). PySide6/Qt dependencies
retain their own licenses. Updates verify the release download and SHA-256 checksum.
