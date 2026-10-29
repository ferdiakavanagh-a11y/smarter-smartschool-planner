"""Compile the checked-in GLSL sources using the installed, matching Qt runtime."""
from pathlib import Path
import subprocess
import os
import PySide6


def main():
    qsb = Path(PySide6.__file__).parent/('qsb.exe' if os.name == 'nt' else 'qsb')
    folder = Path(__file__).resolve().parent/'qml_app/shaders'
    for source in folder.glob('*.frag'):
        subprocess.run([str(qsb), '--qt6', '-o', str(source.with_suffix('.frag.qsb')), str(source)], check=True)


if __name__ == '__main__':
    main()
