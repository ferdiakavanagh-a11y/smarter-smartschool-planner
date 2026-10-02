"""
The actual desktop app: the exe is built from this


(useful for testing before building the .exe)
"""

from __future__ import annotations

import sys
import threading
import traceback
import webbrowser
from pathlib import Path


def get_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


ROOT = get_root()
sys.path.insert(0, str(ROOT))

import json  # noqa: E402

import planner_html  # noqa: E402
import sync  # noqa: E402
import task_state  # noqa: E402
import webview  # noqa: E402
from webview.window import FixPoint  # noqa: E402

MIN_WIDTH, MIN_HEIGHT = 760, 560
DATA_FILE = ROOT / "data" / "planner_data.json"
CREDS_FILE = ROOT / "credentials.yml"


class Api:
    """
    Methods that JavaScript can call through `pywebview.api.*`.

    Keep the window object private. pywebview scans public attributes to find
    callable methods. If it finds the native window object, it may scan deeply
    into its .NET/WinForms internals and get stuck in an endless loop.

    The leading underscore keeps private attributes out of that scan.
    """

    def __init__(self):
        self._window = None
        self._maximized = False

    # ---- window controls (the window is frameless; the page draws the buttons) ----
    def win_close(self):
        self._window.destroy()
        return True

    def win_minimize(self):
        self._window.minimize()
        return True

    def win_toggle_maximize(self):
        if self._maximized:
            self._window.restore()
        else:
            self._limit_maximize_to_work_area()
            self._window.maximize()
        return True

    def win_is_maximized(self):
        return self._maximized

    def win_size(self):
        """Current size in logical pixels - the starting point for a drag-resize."""
        return {"w": self._window.width, "h": self._window.height}

    def win_resize(self, width, height, edge):
        """Resize to width x height, keeping the edge opposite the dragged one fixed."""
        edge = str(edge)
        fix = (FixPoint.EAST if "w" in edge else FixPoint.WEST) | (FixPoint.SOUTH if "n" in edge else FixPoint.NORTH)
        self._window.resize(max(MIN_WIDTH, int(width)), max(MIN_HEIGHT, int(height)), fix)
        return True

    # ---- internals (leading underscore: hidden from the JS bridge) ----
    def _limit_maximize_to_work_area(self):
        """A frameless WinForms window maximizes over the taskbar; keep it inside the work area."""
        try:
            from System import Func, Type  # noqa: PLC0415 - only exists under pythonnet (Windows)
            from System.Drawing import Rectangle  # noqa: PLC0415
            from System.Windows.Forms import Screen  # noqa: PLC0415

            form = self._window.native

            def apply():
                screen = Screen.FromControl(form)
                wa, b = screen.WorkingArea, screen.Bounds
                # MaximizedBounds is relative to the monitor it maximizes on
                form.MaximizedBounds = Rectangle(wa.X - b.X, wa.Y - b.Y, wa.Width, wa.Height)

            form.Invoke(Func[Type](apply))
        except Exception:  # noqa: BLE001 - worst case it covers the taskbar; never break the button
            traceback.print_exc()

    def _tune_window(self):
        """Ask Windows 11 for rounded corners on the frameless window (ignored on Windows 10)."""
        try:
            import ctypes  # noqa: PLC0415

            hwnd = int(self._window.native.Handle.ToInt64())
            pref = ctypes.c_int(2)  # DWMWCP_ROUND
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 33, ctypes.byref(pref), ctypes.sizeof(pref))
        except Exception:  # noqa: BLE001
            pass

    def _set_maximized(self, value):
        self._maximized = value
        try:
            self._window.evaluate_js(f"document.body.classList.toggle('maximized', {'true' if value else 'false'})")
        except Exception:  # noqa: BLE001 - page may be mid-load
            pass

    def _on_maximized(self):
        if not self._maximized:
            self._set_maximized(True)

    def _on_restored(self):
        if self._maximized:
            self._set_maximized(False)

    def sync_now(self):
        threading.Thread(target=do_sync_and_render, args=(self._window,), daemon=True).start()
        return True

    def mark_task(self, task_id, done):
        task_state.set_task_done(ROOT, task_id, bool(done))
        return True

    def open_external(self, url):
        webbrowser.open(url)
        return True

    def save_setting(self, key, value):
        task_state.set_setting(ROOT, str(key), value)
        return True


api = Api()


def do_sync_and_render(window):
    try:
        # Overlay the spinner on whatever page is showing (no full reload flash).
        try:
            window.evaluate_js("showLoading()")
        except Exception:  # noqa: BLE001 - page not ready; fall back to a full load
            window.load_html(planner_html.render_loading(task_state.load_settings(ROOT)))

        if not CREDS_FILE.exists():
            window.load_html(
                planner_html.render_error(
                    "No credentials.yml found next to this program. "
                    "Copy credentials.yml.example to credentials.yml and fill in your "
                    "Smartschool login details, then click Retry.",
                    task_state.load_settings(ROOT),
                )
            )
            return

        data = sync.run(days_back=10, days_ahead=21)
        completed = task_state.load_completed_ids(ROOT)
        html = planner_html.render_html(data, completed, embedded=True, settings=task_state.load_settings(ROOT))
        window.load_html(html)
    except Exception:  # noqa: BLE001 - show the error in-window, don't just vanish
        window.load_html(planner_html.render_error(traceback.format_exc(), task_state.load_settings(ROOT)))


def load_cached_html() -> str:
    """HTML for the last saved data. If there is none (first run) or it's
    unreadable, an empty 'Not synced yet' page - nothing syncs until you press
    the sync button."""
    settings = task_state.load_settings(ROOT)
    if DATA_FILE.exists():
        try:
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            completed = task_state.load_completed_ids(ROOT)
            print(f"Startup: showing saved data from {DATA_FILE} - not syncing.")
            return planner_html.render_html(data, completed, embedded=True, settings=settings)
        except Exception as exc:  # noqa: BLE001 - corrupt/old cache: treat as missing
            print(f"Startup: couldn't use {DATA_FILE} ({exc}).")
    else:
        print(f"Startup: no saved data at {DATA_FILE}.")
    empty = {"todos": [], "days": [], "all_classes": [], "main_url": "", "generated_at": None}
    return planner_html.render_html(empty, [], embedded=True, settings=settings)


def main():
    just_set_up = False
    if "--setup" in sys.argv or not CREDS_FILE.exists():
        import setup_ui  # noqa: PLC0415

        had_file = CREDS_FILE.exists()
        saved = setup_ui.run_setup(CREDS_FILE)
        if not saved and not had_file:
            return  # cancelled on first run: nothing to show
        just_set_up = saved

    window = webview.create_window(
        "Smartschool Planner",
        html=load_cached_html(),  # opens straight on the app; never syncs by itself
        js_api=api,
        width=980,
        height=780,
        min_size=(MIN_WIDTH, MIN_HEIGHT),
        frameless=True,  # no Windows title bar: the page draws its own (see #titlebar / #wc)
        easy_drag=False,  # only the title bar area drags the window (class pywebview-drag-region)
        shadow=True,
    )
    api._window = window
    window.events.shown += api._tune_window
    window.events.maximized += api._on_maximized
    window.events.restored += api._on_restored
    if just_set_up:
        window.events.shown += api.sync_now  # first sync right after saving credentials
    webview.start()


if __name__ == "__main__":
    main()
