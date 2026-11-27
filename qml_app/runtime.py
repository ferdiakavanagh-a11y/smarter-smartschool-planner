"""Production Qt Quick launcher and the existing setup/credential helper modes."""
import os
import sys
import threading
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
    from PySide6.QtCore import QObject, Qt, QTimer, QUrl, Signal
    from PySide6.QtGui import QGuiApplication, QIcon
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuickControls2 import QQuickStyle
    from PySide6.QtWebEngineQuick import QtWebEngineQuick
    QQuickStyle.setStyle('Basic')
    QtWebEngineQuick.initialize()
    application = QGuiApplication(sys.argv)
    application.setApplicationName('Smartschool Planner')
    resources = Path(getattr(sys, '_MEIPASS', root))
    application.setWindowIcon(QIcon(str(resources/'assets/icon.ico')))
    import task_state
    from .model import Stopwatch
    from .main import round_window
    engine = QQmlApplicationEngine()
    context = engine.rootContext()
    settings = task_state.load_settings(root)
    for key, value in dict(backend=None, tasks=None, stopwatch=None,
                           startupPreferences=settings, initialCount=0, initialFancy=True,
                           initialMatched=False, benchmarkEnabled=False).items():
        context.setContextProperty(key, value)
    engine.load(QUrl.fromLocalFile(str(resources/'qml_app/Main.qml')))
    if not engine.rootObjects():
        return 1
    window = engine.rootObjects()[0]
    window.visibilityChanged.connect(lambda _: round_window(window))

    class WorkspaceImport(QObject):
        finished = Signal(object)

    workspace_import = WorkspaceImport()
    importing = False
    closing = threading.Event()
    backend = None
    startup_jobs_started = False
    startup_fallback = QTimer(window, singleShot=True, interval=2000)

    def attach_workspace(backend_class):
        nonlocal backend
        if backend_class is None:
            window.setProperty('workspaceLoadFailed', True)
            return
        try:
            backend = backend_class(root)
        except Exception:
            window.setProperty('workspaceLoadFailed', True)
            return
        backend.sync_after_choice = saved
        context.setContextProperty('tasks', backend.tasks)
        context.setContextProperty('stopwatch', Stopwatch())
        context.setContextProperty('backend', backend)
        startup_fallback.start()

    def start_workspace_import():
        nonlocal importing
        if importing:
            return
        importing = True
        startup_fallback.stop()

        def load_backend_class():
            try:
                from .backend import Backend
            except Exception:
                Backend = None
            if not closing.is_set():
                workspace_import.finished.emit(Backend)

        threading.Thread(target=load_backend_class, daemon=True).start()

    workspace_import.finished.connect(attach_workspace, Qt.QueuedConnection)

    def start_background_jobs():
        nonlocal startup_jobs_started
        if startup_jobs_started:
            return
        startup_jobs_started = True
        startup_fallback.stop()
        window.frameSwapped.disconnect(on_frame)
        backend.startUpdates()
        if backend.sync_after_choice and not task_state.rendering_choice_pending(root):
            backend.sync_after_choice = False
            backend.syncNow()
        QTimer.singleShot(120, window, backend.features.refresh_inbox_on_open)
        QTimer.singleShot(240, window, backend.preloadNotes)

    def on_frame():
        if backend is None:
            start_workspace_import()
        elif window.property('startupPageReady'):
            start_background_jobs()

    def on_timeout():
        if backend is None:
            start_workspace_import()
        else:
            start_background_jobs()

    startup_fallback.timeout.connect(on_timeout)
    window.frameSwapped.connect(on_frame, Qt.QueuedConnection)
    window.show()
    window.requestActivate()
    startup_fallback.start()
    try:
        code = application.exec()
    finally:
        closing.set()
        if backend is not None:
            backend.shutdown()
    del engine
    return code
