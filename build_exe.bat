@echo off
REM Builds SmartschoolPlanner.exe from desktop_app.py. Rerun after any .py change. See BUILD_EXE.md.

cd /d "%~dp0"

echo Installing/updating PyInstaller...
python -m pip install pyinstaller --upgrade
if errorlevel 1 (
    echo.
    echo ERROR: Could not install or update PyInstaller.
    pause
    exit /b 1
)

echo.
echo Building SmartschoolPlanner.exe ...

REM assets\ holds icon.ico (exe icon) and the window-button SVGs, bundled into the exe.
REM An existing .spec can't take --icon/--add-data, so build from the command line (rewrites the .spec).
set "ICON_FILE=assets\icon.ico"
if not exist "%ICON_FILE%" if exist "icon.ico" set "ICON_FILE=icon.ico"

set "ICON_ARG="
if exist "%ICON_FILE%" set ICON_ARG=--icon="%ICON_FILE%"
set "ASSETS_ARG="
if exist "assets\" set ASSETS_ARG=--add-data "assets;assets"

REM Always regenerate the spec: an old one may still request a one-file bundle.
    python -m PyInstaller --clean --noconfirm --onedir --noupx --windowed --name SmartschoolPlanner %ICON_ARG% %ASSETS_ARG% ^
        --hidden-import=pydantic ^
        --hidden-import=bs4 ^
        --hidden-import=yaml ^
        --hidden-import=pyotp ^
        --hidden-import=logprise ^
        --hidden-import=clr ^
        --hidden-import=clr_loader ^
        --hidden-import=webview.platforms.edgechromium ^
        --collect-all pythonnet ^
        --collect-all webview ^
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
xcopy /E /I /Y "dist\SmartschoolPlanner\_internal" "_internal" >nul
if errorlevel 1 exit /b 1
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
