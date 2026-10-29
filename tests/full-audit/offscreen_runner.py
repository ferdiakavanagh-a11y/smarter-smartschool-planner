"""Run existing synthetic QML checks with an enforced offscreen platform and fonts."""
import argparse
import json
import os
import runpy
import sys
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--renderer', choices=('software', 'd3d11'), default='software')
parser.add_argument('--probe', action='store_true', help='Capture real Main.qml without the full stress suite')
parser.add_argument('--script', default='qml_ui_issues.py', help='Existing synthetic script in tests/')
parser.add_argument('--test-arg', action='append', default=[])
args = parser.parse_args()
target = (ROOT / 'tests' / args.script).resolve()
if target.parent != ROOT / 'tests' or target.suffix != '.py':
    parser.error('Choose a Python test script directly inside tests/')
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['QSG_RENDER_LOOP'] = 'basic'
os.environ['QSG_RHI_BACKEND'] = 'd3d11'
os.environ['QT_QUICK_BACKEND'] = 'software' if args.renderer == 'software' else 'rhi'
os.environ['PYTHONUTF8'] = '1'
if os.name == 'nt':
    import ctypes
    ctypes.windll.kernel32.SetErrorMode(0x0001 | 0x0002)
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
from PySide6 import QtGui
from PySide6.QtQuick import QQuickWindow, QSGRendererInterface

QQuickWindow.setGraphicsApi(QSGRendererInterface.Software if args.renderer == 'software' else QSGRendererInterface.Direct3D11)
evidence = ROOT / 'tests/full-audit' / ('offscreen-' + args.renderer)
evidence.mkdir(exist_ok=True)
metadata = dict(requested_renderer=args.renderer, platform='offscreen', fonts=[],
                capture_method='QQuickItem.grabToImage' if args.renderer == 'd3d11' else 'QQuickWindow.grabWindow')
RealApplication = QtGui.QGuiApplication


class OffscreenApplication(RealApplication):
    def __init__(self, values):
        super().__init__(values)
        if self.platformName() != 'offscreen':
            raise RuntimeError('Refusing to run without the offscreen platform')
        folder = Path('C:/Windows/Fonts')
        for name in ['SegUIVar.ttf', 'segoeui.ttf', 'segoeuib.ttf', 'seguisb.ttf',
                     'segoeuii.ttf', 'seguiemj.ttf', 'seguisym.ttf', 'meiryo.ttc',
                     'msgothic.ttc', 'msyh.ttc', 'YuGothR.ttc', 'malgun.ttf',
                     'LeelawUI.ttf', 'LEELAWAD.TTF', 'tahoma.ttf']:
            path = folder / name
            if path.is_file():
                font_id = QtGui.QFontDatabase.addApplicationFont(str(path))
                metadata['fonts'].append(dict(file=name, id=font_id, families=QtGui.QFontDatabase.applicationFontFamilies(font_id)))
        self.setFont(QtGui.QFont('Segoe UI Variable'))
        metadata['font_family_count'] = len(QtGui.QFontDatabase.families())


def grab_content(window):
    if RealApplication.platformName() != 'offscreen':
        raise RuntimeError('Refusing a capture outside the offscreen platform')
    from PySide6.QtTest import QTest
    grabbed = window.contentItem().grabToImage()
    if not grabbed:
        raise RuntimeError('Offscreen content capture could not start')
    done = []
    grabbed.ready.connect(lambda: done.append(True))
    for _ in range(40):
        if done:
            break
        QTest.qWait(50)
    if not done or grabbed.image().isNull():
        raise RuntimeError('Offscreen content capture did not finish within two seconds')
    return grabbed.image()


def capture(window):
    metadata.update(platform=RealApplication.platformName(),
                    actual_renderer=str(window.rendererInterface().graphicsApi()),
                    scene_graph_initialized=window.isSceneGraphInitialized(),
                    exposed=window.isExposed(), scene_ready=window.property('sceneReady'),
                    size=[window.width(), window.height()])
    image = window.grabWindow()
    metadata['image_null'] = image.isNull()
    if not image.isNull():
        metadata['capture'] = str(evidence / 'main.png')
        assert image.save(metadata['capture'])
        metadata['sampled_colors'] = len({image.pixelColor(x, y).rgba() for x in range(0, image.width(), 19) for y in range(0, image.height(), 19)})
    (evidence / 'metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(json.dumps(metadata), flush=True)


sys.argv = [str(target), *args.test_arg]
with ExitStack() as patches:
    patches.enter_context(patch.object(QtGui, 'QGuiApplication', OffscreenApplication))
    if args.renderer == 'd3d11':
        patches.enter_context(patch.object(QQuickWindow, 'grabWindow', grab_content))
    if args.probe:
        source = (ROOT / 'tests/qml_ui_issues.py').read_text(encoding='utf-8').split("if '--interactive' in sys.argv:")[0]
        state = dict(__file__=str(ROOT / 'tests/qml_ui_issues.py'), __name__='__main__')
        exec(compile(source, state['__file__'], 'exec'), state)
        state['fixtures'].choose('Worst case')
        state['QTest'].qWait(900)
        capture(state['window'])
        state['backend'].shutdown()
        state['window'].hide()
        state['toggle'].hide()
        state['mock'].stop()
    else:
        # The existing script owns all input, fixtures, assertions and normal evidence.
        state = runpy.run_path(str(target), run_name='__main__')
        from shiboken6 import isValid
        if 'window' in state and isValid(state['window']) and state['window'].isVisible():
            capture(state['window'])
        else:
            metadata['completed_script'] = args.script
            (evidence / 'metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
