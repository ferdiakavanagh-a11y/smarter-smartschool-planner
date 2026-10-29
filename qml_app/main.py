"""Run with the isolated interpreter; no production imports or private data access."""
import time
STARTED = time.perf_counter()
import argparse
import json
import os
import sys
from pathlib import Path

os.environ.setdefault('QSG_RHI_BACKEND', 'd3d11')
# This Windows host stalls idle-to-animation transitions with the threaded loop.
os.environ.setdefault('QSG_RENDER_LOOP', 'basic')
os.environ.setdefault('QSG_INFO', '1')
from PySide6.QtCore import QTimer, QUrl, qVersion, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
try:
    from .model import Tasks, Stopwatch
except ImportError:
    from model import Tasks, Stopwatch


def round_window(window):
    """Let the Windows compositor smooth the outer edge without a render layer."""
    if sys.platform != 'win32' or sys.getwindowsversion().build < 22000 or not window.isVisible():
        return False
    import ctypes
    set_attribute = ctypes.WinDLL('dwmapi').DwmSetWindowAttribute
    set_attribute.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_uint]
    set_attribute.restype = ctypes.c_long
    # DWMWA_WINDOW_CORNER_PREFERENCE / DWMWCP_ROUND; maximized edges remain square.
    preference = ctypes.c_int(2)
    result = set_attribute(int(window.winId()), 33, ctypes.byref(preference), ctypes.sizeof(preference))
    if result < 0:
        print(f'Native window rounding unavailable (HRESULT {result:#x})', file=sys.stderr)
    return result >= 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--count', type=int, choices=(0, 36, 1000), default=36)
    parser.add_argument('--mode', choices=('fancy', 'performance'), default='fancy')
    parser.add_argument('--benchmark', action='store_true')
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--matched', action='store_true', help='Static shared backdrop and no refraction for the comparison experiment')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'artifacts')
    args = parser.parse_args()
    if not all((Path(__file__).parent / ('shaders/'+name+'.frag.qsb')).exists() for name in ('glass','wallpaper')):
        parser.error('Compile the shader first: see setup.ps1 / README.md')
    QQuickStyle.setStyle('Basic')
    app = QGuiApplication(sys.argv)
    model = Tasks(args.count)
    stopwatch = Stopwatch()
    engine = QQmlApplicationEngine()
    context = engine.rootContext()
    for name, value in dict(tasks=model, stopwatch=stopwatch, initialCount=args.count,
                            initialFancy=args.mode == 'fancy', initialMatched=args.matched, benchmarkEnabled=args.benchmark).items():
        context.setContextProperty(name, value)
    engine.load(QUrl.fromLocalFile(str(Path(__file__).with_name('Main.qml').resolve())))
    if not engine.rootObjects():
        return 1
    window = engine.rootObjects()[0]
    window.setScreen(app.primaryScreen())
    area = app.primaryScreen().availableGeometry()
    window.setPosition(area.x() + 32, area.y() + 32)
    window.resize(1100, 800)
    window.visibilityChanged.connect(lambda _: round_window(window))
    window.show()
    window.requestActivate()
    result = dict(runtime=qVersion(), python=sys.version, render_loop=os.environ['QSG_RENDER_LOOP'], count=args.count, mode=args.mode, matched=args.matched,
                  dpr=window.devicePixelRatio(), size=[window.width(), window.height()], frames={})
    first = [True]

    def ready():
        if not first[0] or not window.property('sceneReady'):
            return
        first[0] = False
        window.frameSwapped.disconnect(ready)
        result['startup_ms'] = (time.perf_counter() - STARTED) * 1000
        result['dpr'] = window.devicePixelRatio()
        result['size'] = [window.width(), window.height()]
        if args.benchmark and result['size'] != [1100, 800]:
            print('Benchmark viewport changed: ' + str(result['size']), file=sys.stderr, flush=True)
            app.exit(1)
            return
        result['refresh_rate_hz'] = window.screen().refreshRate()
        result['window_active'] = window.isActive()
        result['color_scheme'] = 'dark' if window.property('appearance').property('dark') else 'light'
        result['graphics_api'] = str(window.rendererInterface().graphicsApi())
        print(json.dumps({'ready': result}), flush=True)
        QTimer.singleShot(0, start_checks)

    window.frameSwapped.connect(ready, Qt.QueuedConnection)
    def start_checks():
        if not (args.benchmark or args.smoke):
            return
        args.output.mkdir(parents=True, exist_ok=True)

        def save():
            (args.output / 'qml.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
            app.quit()

        def capture(name):
            if not window.grabWindow().save(str(args.output / (name + '.png'))):
                raise RuntimeError('Could not capture application window')

        def phase(action):
            print(json.dumps({'phase': action}), flush=True)
            window.bench(action)

        def collect(name):
            result['frames'][name] = window.property('frameSamples').toVariant()
            phase('idle')

        if args.benchmark:
            QTimer.singleShot(2000, lambda: phase('scroll'))
            QTimer.singleShot(6200, lambda: collect('scroll'))
            QTimer.singleShot(7000, lambda: phase('transition'))
            QTimer.singleShot(11000, lambda: collect('transition'))
            def search():
                start = time.perf_counter()
                phase('search')
                def painted():
                    window.frameSwapped.disconnect(painted)
                    result['search_to_frame_ms'] = (time.perf_counter() - start) * 1000
                window.frameSwapped.connect(painted, Qt.QueuedConnection)
            QTimer.singleShot(11500, search)
            QTimer.singleShot(12500, lambda: phase('clearSearch'))
            QTimer.singleShot(14000, lambda: phase('settled_idle'))
            QTimer.singleShot(20000, save)
        else:
            QTimer.singleShot(1000, lambda: capture('planner'))
            QTimer.singleShot(1300, lambda: phase('settings'))
            QTimer.singleShot(1900, lambda: capture('settings'))
            QTimer.singleShot(2200, lambda: phase('closeSettings'))
            QTimer.singleShot(2500, lambda: phase('focus'))
            QTimer.singleShot(3800, lambda: capture('focus'))
            QTimer.singleShot(4200, save)
    code = app.exec()
    # Destroy QML bindings before their Python context objects.
    del engine
    return code


if __name__ == '__main__':
    sys.exit(main())
