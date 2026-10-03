@echo off
REM One click: installs dependencies, then runs build_exe.bat,
REM then builds the installer too if Inno Setup 6 is installed.

cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.11+ and tick "Add python.exe to PATH".
    pause
    exit /b 1
)

echo Installing dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Dependency install failed.
    pause
    exit /b 1
)

call build_exe.bat
if not exist "SmartschoolPlanner.exe" (
    echo ERROR: SmartschoolPlanner.exe was not built.
    pause
    exit /b 1
)

set "ISCC="
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"

if "%ISCC%"=="" (
    echo.
    echo Inno Setup 6 not found - skipping installer. SmartschoolPlanner.exe is ready.
    pause
    exit /b 0
)

"%ISCC%" SmartschoolPlanner.iss
if errorlevel 1 (
    echo ERROR: Inno Setup failed.
    pause
    exit /b 1
)

echo.
echo Done: installer_output\SmartschoolPlanner-Setup.exe
pause
