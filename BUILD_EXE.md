# Build the Windows application

Use Windows and Python 3.12. Run `build_exe.bat` to install the locked
`requirements-release.txt`, compile the Qt shaders, and build an onedir app.
It copies `SmartschoolPlanner.exe` and its required `_internal` folder beside
the source files. Keep both together.

Release dependencies must have compatible wheels: the install refuses source
distributions instead of executing their build scripts. If a wheel is missing,
review the package and build environment before updating the pins; do not remove
the binary-only gate. Pins currently have no locally reviewed artifact hashes,
so this gate does not establish package integrity. See pip's
[secure-install guidance](https://pip.pypa.io/en/stable/topics/secure-installs/).

`setup_and_build.bat` also builds the installer if Inno Setup 6 is installed.
CI invokes the same executable build before compiling the installer. Existing
version, checksum and verified-publisher gates are retained.

The desktop entry is `desktop_app.py`. QML, `qmldir`, `Icons.js`, wallpaper SVG
and compiled shaders are included explicitly. Development `.venv` directories,
benchmark evidence and account data are excluded. PyInstaller's Qt hooks
collect Qt plugins and QML imports. GLSL sources are kept in Git; `.qsb` files
are generated using the pinned PySide6 version during every build.

Rebuild after Python, QML, icon or shader changes. A fresh source clone requires
`python compile_shaders.py` after installing requirements.

The app uses Qt Quick instead of WebView2/pythonnet. Installer identity, data
paths, helper switches, credential cleanup and checksum verification remain.
Before publishing, check the packaged app and actual upgrade/uninstall lifecycle.
