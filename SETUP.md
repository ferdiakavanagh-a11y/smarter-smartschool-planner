# Windows setup

Use Python 3.12 and open PowerShell in this folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python compile_shaders.py
python desktop_app.py
```

On first launch, enter your login in the protected setup window and choose Fancy
or Performance. Local date checking needs no Gemini key. An optional API key can
be configured in the login window.

Settings contains Change login details, date checking, themes, rendering,
backgrounds, text sizes, accessibility and Copy sync diagnostics.

Normal startup reads the last snapshot only if its account matches the current
credentials. Use Sync for a network refresh. Existing snapshot and task-state
files under `data/` remain compatible. Login secrets stay in Windows credential
storage and encrypted sessions; do not share credentials or the data folder.

The Qt interface needs a working graphics driver. Performance mode freezes the
wallpaper and reduces shader sampling. WebView2 is no longer used.

For an unattended source-folder refresh, Task Scheduler can still run
`run_daily.bat`; it invokes `sync.py` without opening the interface.

Installed Start Menu login-details shortcuts and `--setup` remain available.
Settings uses `--setup-only` for its independent credential helper. The installer
uses `--clear-credentials` during uninstall. Installers from existing GitHub
releases continue to contain their original interface until a new release is
explicitly built and published.
