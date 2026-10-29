# Qt Quick interface

Production launches through `desktop_app.py` in the repository root. Install the
root requirements, run `python compile_shaders.py`, then start the desktop app.
See the root README, SETUP.md and BUILD_EXE.md for account and packaging details.

The QML view is connected to real snapshot/state services through `runtime.py`,
`backend.py`, `production_model.py` and `sections.py`. `SelectorLens.qml` is shared
by the slider handles and top-row buttons. `Glass.qml` and the two GLSL shaders
implement the optical surfaces and procedural wallpaper.

## Synthetic development harness

For isolated visual work without credentials or production state:

```powershell
powershell -ExecutionPolicy Bypass -File qml_app/setup.ps1
& './qml_app/.venv/Scripts/python.exe' -m qml_app.main --count 36
```

Optional harness flags include `--count 0`, `--count 1000`, `--mode performance`
and `--smoke`. Harness edits are memory-only. Production never selects these
fixtures. The `.venv`, generated shader binaries and evidence remain ignored.

The interface uses native Qt controls, queued service callbacks, list
virtualization, independent frosting/distortion, four procedural backgrounds,
reduced motion, high contrast and an opaque shader-error fallback. Frame timing
limits from the earlier prototype still apply; integration does not establish a
new performance advantage or 60 fps guarantee.

Background choices are Satin (indigo/pearl folds), Soft colours (the original
colour fields), Tide (blue glass waves) and Dunes (warm pearl/mauve folds).
Each has a light and dark appearance and uses the existing animation controls.

## Attribution

See THIRD_PARTY_NOTICES.md and preserve the adapted material code's MIT notices.
