param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
$prototype = $PSScriptRoot
& $Python -m venv "$prototype/.venv"
if ($LASTEXITCODE -ne 0) { throw 'Creating the isolated environment failed' }
& "$prototype/.venv/Scripts/python.exe" -m pip install -r "$prototype/requirements.txt"
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
& "$prototype/.venv/Scripts/pyside6-qsb.exe" --qt6 -o "$prototype/shaders/glass.frag.qsb" "$prototype/shaders/glass.frag"
if ($LASTEXITCODE -ne 0) { throw 'Windows shader compilation failed' }
& "$prototype/.venv/Scripts/pyside6-qsb.exe" --qt6 -o "$prototype/shaders/wallpaper.frag.qsb" "$prototype/shaders/wallpaper.frag"
if ($LASTEXITCODE -ne 0) { throw 'Background shader compilation failed' }
