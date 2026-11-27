"""Build file-relative QML caches with the Qt version shipped by PySide6."""
import os
from pathlib import Path
import subprocess

import PySide6


def main():
    root = Path(__file__).resolve().parent
    sources = root / 'qml_app'
    output = root / 'build' / 'qml-cache'
    output.mkdir(parents=True, exist_ok=True)
    for cache in [*output.glob('*.qmlc'), *output.glob('*.jsc')]:
        cache.unlink()
    compiler = Path(PySide6.__file__).with_name(
        'qmlcachegen.exe' if os.name == 'nt' else 'qmlcachegen'
    )
    environment = dict(os.environ, QT_COMMAND_LINE_PARSER_NO_GUI_MESSAGE_BOXES='1')
    for source in sorted([*sources.glob('*.qml'), *sources.glob('*.js')]):
        subprocess.run(
            [str(compiler), '-o', str(output / (source.name + 'c')), source.name],
            cwd=sources,
            env=environment,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            check=True,
        )


if __name__ == '__main__':
    main()
