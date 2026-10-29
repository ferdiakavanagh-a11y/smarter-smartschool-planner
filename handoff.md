# Smartschool Planner 3.0.0 handoff

Production launches through desktop_app.py and qml_app/runtime.py. The Qt Quick
interface replaces the removed HTML/WebView renderer. Build with build_exe.bat;
GLSL is compiled with the matching pinned Qt runtime by compile_shaders.py.
Do not commit credentials, data, virtual environments or generated binaries.

Defaults: Clear Light and Soft colours. Saved appearance settings remain intact.
Satin, Tide and Dunes are original procedural artwork; independent frosting and
distortion, reduced motion and high contrast remain available.

Local task updates reconcile stable task IDs rather than reset the list, retaining
reading position. State is saved before presentation changes. Account identity
parsing accepts inline Smartschool JSON bootstrap scripts without the obsolete
jQuery extend marker. Existing account validation and private-data guards remain.

Known startup issues, reviewed but deliberately left unchanged at user request:
- Manual upgrades can omit patch notes when installer launch is skipped.
- Upgrades clear a still-pending first rendering choice.

Code signing remains pending. The release publication gate intentionally rejects
unsigned installers; do not bypass it. Pushing source does not update installed EXEs.

Local regressions use qml_app/.venv/Scripts/python.exe with PYTHONPATH pointing to
tests/startup-deps and writable TEMP/TMP=tests/check-temp. Native UI tests must use
tests/full-audit/offscreen_runner.py; no desktop interaction was requested.
Unit suites: unittest discover -s tests -p test_*.py and the release_tests suite.

V3 verification: 130 Python and 29 release tests pass; shaders compile; offscreen
scroll/reading-anchor regression passes in both rendering modes. Release tests
passed on retry after a Windows monitor-file cleanup race. No installer was built.
