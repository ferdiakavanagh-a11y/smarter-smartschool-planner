# Smartschool Planner 3.0.0

A Windows desktop planner with a native Qt Quick interface and liquid glass
controls. It uses the existing Smartschool sync backend and keeps your planner
snapshot, completion, pins and private notes on your computer.

## Run

Use Python 3.12 on Windows:

```powershell
python -m pip install -r requirements.txt
python compile_shaders.py
python desktop_app.py
```

The first launch opens protected account setup. Select Fancy or Performance;
the initial sync runs after successful first-time setup and a rendering choice.
Later launches show the last verified account snapshot without automatically
syncing. Use the top Sync button to refresh your data.

The source entry point and installed executable use the same Qt interface.
WebView2 and pythonnet are no longer required. See [setup](SETUP.md) and
[building the Windows executable](BUILD_EXE.md).

## Features

- Planner and Missed tasks, course/type/pinned filters, week overview,
  completion/undo, pins, durable notes and original assignment details.
- Schedule and All Classes from the sync snapshot, with linked tasks.
- Published grades, weighted counting totals and feedback.
- LVS notes and absences, account/year-scoped read state, mark-all-read and
  on-demand details. Existing private/deleted/denied-record protections remain.
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
