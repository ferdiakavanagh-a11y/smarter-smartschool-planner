"""Production Qt Quick launcher and the existing setup/credential helper modes."""
import os
import sys
from pathlib import Path


def get_root():
    return Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[1]


def main():
    root = get_root()
    credentials = root/'credentials.yml'
    if '--clear-credentials' in sys.argv:
        import credential_store
        credential_store.clear_credentials(credentials)
        return 0
    if '--setup-only' in sys.argv:
        import setup_ui
        return 0 if setup_ui.run_setup(credentials) else 1
    import credential_store
    needs_setup = '--setup' in sys.argv or not credentials.exists()
    if not needs_setup:
        try:
            credential_store.load_credentials(credentials)
        except (OSError, credential_store.CredentialError):
            needs_setup = True
    saved = False
    if needs_setup:
        import setup_ui
        saved = setup_ui.run_setup(credentials)
        if not saved and not credentials.exists():
            return 0
    os.environ.setdefault('QSG_RHI_BACKEND', 'd3d11')
    os.environ.setdefault('QSG_RENDER_LOOP', 'basic')
    from PySide6.QtCore import QTimer, QUrl
    from PySide6.QtGui import QGuiApplication, QIcon
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuickControls2 import QQuickStyle
    from .backend import Backend
    from .model import Stopwatch
    from .main import round_window
    QQuickStyle.setStyle('Basic')
    application = QGuiApplication(sys.argv)
    application.setApplicationName('Smartschool Planner')
    resources = Path(getattr(sys, '_MEIPASS', root))
    application.setWindowIcon(QIcon(str(resources/'assets/icon.ico')))
    backend = Backend(root)
    backend.sync_after_choice = saved
    stopwatch = Stopwatch()
    engine = QQmlApplicationEngine()
    for key, value in dict(backend=backend, tasks=backend.tasks, stopwatch=stopwatch,
                           initialCount=0, initialFancy=True, initialMatched=False, benchmarkEnabled=False).items():
        engine.rootContext().setContextProperty(key, value)
    engine.load(QUrl.fromLocalFile(str(resources/'qml_app/Main.qml')))
    if not engine.rootObjects():
        return 1
    window = engine.rootObjects()[0]
    window.visibilityChanged.connect(lambda _: round_window(window))
    window.show()
    window.requestActivate()
    QTimer.singleShot(0, backend.startUpdates)
    if saved and not __import__('task_state').rendering_choice_pending(root):
        backend.sync_after_choice = False
        QTimer.singleShot(0, backend.syncNow)
    application.aboutToQuit.connect(backend.shutdown)
    code = application.exec()
    backend.shutdown()
    del engine
    return code
