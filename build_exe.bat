@echo off
setlocal DisableDelayedExpansion
REM Builds SmartschoolPlanner.exe from desktop_app.py. Rerun after any .py change. See BUILD_EXE.md.

cd /d "%~dp0"

python -c "import sys, sysconfig; sys.exit(not (sys.implementation.name == 'cpython' and sys.version_info[:2] == (3, 14) and sysconfig.get_platform() == 'win-amd64' and not sysconfig.get_config_var('Py_GIL_DISABLED')))"
if errorlevel 1 (
    echo ERROR: Activate a standard 64-bit Windows CPython 3.14 environment first.
    exit /b 1
)
python -c "import tkinter; tkinter.Tcl()"
if errorlevel 1 (
    echo ERROR: The build interpreter needs Tcl/Tk for the account setup window.
    exit /b 1
)

echo Installing locked runtime and build dependencies...
python -m pip install --only-binary=:all: --no-deps -r requirements-release.txt
if errorlevel 1 (
    echo.
    echo ERROR: Could not install the locked release dependencies.
    pause
    exit /b 1
)

python -m pip check
if errorlevel 1 exit /b 1

echo.
echo Building SmartschoolPlanner.exe ...

python compile_shaders.py
if errorlevel 1 exit /b 1

REM assets\ holds icon.ico (exe icon) and shared application artwork, bundled into the exe.
REM An existing .spec can't take --icon/--add-data, so build from the command line (rewrites the .spec).
set "ICON_FILE=assets\icon.ico"
if not exist "%ICON_FILE%" if exist "icon.ico" set "ICON_FILE=icon.ico"

set "ICON_ARG="
if exist "%ICON_FILE%" set ICON_ARG=--icon="%ICON_FILE%"
set "ASSETS_ARG="
if exist "assets\" set ASSETS_ARG=--add-data "assets;assets"

REM Always regenerate the spec: an old one may still request a one-file bundle.
REM Keep third-party DLL directories on the caller's PATH out of PyInstaller's search.
set "BUILD_PYTHON_PATH="
for /f "delims=" %%P in ('python -c "import pathlib, sys; print(str(pathlib.Path(sys.executable).parent) + ';' + sys.base_prefix)"') do set "BUILD_PYTHON_PATH=%%P"
if not defined BUILD_PYTHON_PATH exit /b 1
set "PATH=%BUILD_PYTHON_PATH%;%SystemRoot%\System32;%SystemRoot%"
set "PYTHONPATH="
python compile_qml.py
if errorlevel 1 exit /b 1
    python -m PyInstaller --clean --noconfirm --onedir --noupx --windowed --name SmartschoolPlanner %ICON_ARG% %ASSETS_ARG% ^
        --hidden-import=pydantic ^
        --hidden-import=bs4 ^
        --hidden-import=yaml ^
        --hidden-import=pyotp ^
        --hidden-import=logprise ^
        --add-data "qml_app/*.qml;qml_app" ^
        --add-data "qml_app/qmldir;qml_app" ^
        --add-data "qml_app/*.js;qml_app" ^
        --add-data "build/qml-cache/*.qmlc;qml_app" ^
        --add-data "build/qml-cache/*.jsc;qml_app" ^
        --add-data "qml_app/*.svg;qml_app" ^
        --add-data "qml_app/shaders/*.qsb;qml_app/shaders" ^
        --add-data "qml_app/THIRD_PARTY_NOTICES.md;qml_app" ^
        --hidden-import=PySide6.QtQml ^
        --hidden-import=PySide6.QtQuick ^
        --hidden-import=PySide6.QtQuickControls2 ^
        --hidden-import=PySide6.QtWebEngineQuick ^
        --hidden-import=PySide6.QtPdf ^
        --collect-all google.genai ^
        --collect-all google.auth ^
        --collect-all httpx ^
        desktop_app.py
if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller failed. The executable was not built.
    pause
    exit /b 1
)

echo.
echo Done. Copying the exe next to your other files...
if not exist "dist\SmartschoolPlanner\SmartschoolPlanner.exe" (
    echo.
    echo ERROR: PyInstaller finished without creating the executable.
    pause
    exit /b 1
)
REM Copy support files first; the executable needs _internal beside it.
if not exist "dist\SmartschoolPlanner\_internal\python314.dll" (
    echo ERROR: The bundled CPython 3.14 runtime is missing.
    exit /b 1
)
if not exist "dist\SmartschoolPlanner\_internal\_tkinter.pyd" (
    echo ERROR: The bundled Tcl/Tk extension for account setup is missing.
    exit /b 1
)
for %%F in (qml_app\*.qml qml_app\*.js qml_app\*.svg qml_app\qmldir) do (
    if not exist "dist\SmartschoolPlanner\_internal\qml_app\%%~nxF" (
        echo ERROR: Missing bundled resource %%F
        exit /b 1
    )
)
for %%F in (qml_app\*.qml qml_app\*.js) do (
    if not exist "dist\SmartschoolPlanner\_internal\qml_app\%%~nxFc" (
        echo ERROR: Missing bundled QML cache %%~nxFc
        exit /b 1
    )
)
for %%F in (qml_app\shaders\*.frag) do (
    if not exist "dist\SmartschoolPlanner\_internal\qml_app\shaders\%%~nxF.qsb" (
        echo ERROR: Missing bundled shader %%~nxF.qsb
        exit /b 1
    )
)
robocopy "dist\SmartschoolPlanner\_internal" "_internal" /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP
if errorlevel 8 exit /b 1
copy /Y "dist\SmartschoolPlanner\SmartschoolPlanner.exe" "."
if errorlevel 1 (
    echo.
    echo ERROR: Could not copy the executable into this folder.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Build complete: SmartschoolPlanner.exe and _internal are now in this folder.
echo You can delete the "build" and "dist" folders and the
echo .spec file if you want to tidy up - they're just build
echo leftovers. Keep _internal beside the exe - it is required to run.
echo ============================================================
pause
exit /b 0
