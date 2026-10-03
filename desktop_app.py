"""Native desktop window for the planner UI (exe entry point). Run: python desktop_app.py"""

from __future__ import annotations

import sys
import threading
import traceback
import webbrowser
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from System import Func, Type  # type: ignore[import-not-found]
    from System.Drawing import Rectangle  # type: ignore[import-not-found]
    from System.Windows.Forms import Screen  # type: ignore[import-not-found]


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
    """Methods callable from the page JS. Never store the window as a public attribute
    (pywebview's bridge recurses into it forever); use a leading underscore."""

    def __init__(self):
        self._window = None
        self._maximized = False

    # window controls
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
        """Current size in logical pixels."""
        return {"w": self._window.width, "h": self._window.height}

    def win_resize(self, width, height, edge):
        """Resize to width x height, keeping the opposite edge fixed."""
        edge = str(edge)
        fix = (FixPoint.EAST if "w" in edge else FixPoint.WEST) | (FixPoint.SOUTH if "n" in edge else FixPoint.NORTH)
        self._window.resize(max(MIN_WIDTH, int(width)), max(MIN_HEIGHT, int(height)), fix)
        return True

    # internals (hidden from the JS bridge)
    def _limit_maximize_to_work_area(self):
        """Keep maximize inside the work area, not over the taskbar."""
        try:
            from System import Func, Type  # noqa: PLC0415 - Windows only  # type: ignore[import-not-found]
            from System.Drawing import Rectangle  # noqa: PLC0415  # type: ignore[import-not-found]
            from System.Windows.Forms import Screen  # noqa: PLC0415  # type: ignore[import-not-found]

            form = self._window.native

            def apply():
                screen = Screen.FromControl(form)
                wa, b = screen.WorkingArea, screen.Bounds
                # relative to the current monitor
                form.MaximizedBounds = Rectangle(wa.X - b.X, wa.Y - b.Y, wa.Width, wa.Height)

            form.Invoke(Func[Type](apply))
        except Exception:  # noqa: BLE001 - best effort
            traceback.print_exc()

    def _tune_window(self):
        """Request Windows 11 rounded corners (ignored on Windows 10)."""
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
        except Exception:  # noqa: BLE001 - mid-load
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
        url = str(url)
        if not url.startswith(("https://", "http://")):  # http/https only
            return False
        webbrowser.open(url)
        return True

    def pin_task(self, task_id, pinned):
        task_state.set_task_pinned(ROOT, str(task_id), bool(pinned))
        return True

    def save_note(self, task_id, text):
        task_state.set_note(ROOT, str(task_id), str(text or ""))
        return True

    def save_setting(self, key, value):
        task_state.set_setting(ROOT, str(key), value)
        return True


api = Api()


def do_sync_and_render(window):
    try:
        # spinner overlay, no reload flash
        try:
            window.evaluate_js("showLoading()")
        except Exception:  # noqa: BLE001 - fall back to full load
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
        html = planner_html.render_html(
            data, completed, embedded=True, settings=task_state.load_settings(ROOT),
            pinned=task_state.load_pinned_ids(ROOT), notes=task_state.load_notes(ROOT),
        )
        window.load_html(html)
    except Exception:  # noqa: BLE001 - show error in-window
        window.load_html(planner_html.render_error(traceback.format_exc(), task_state.load_settings(ROOT)))


def load_cached_html() -> str:
    """HTML for the last saved data, or an empty 'Not synced yet' page. Never syncs."""
    settings = task_state.load_settings(ROOT)
    if DATA_FILE.exists():
        try:
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            completed = task_state.load_completed_ids(ROOT)
            print(f"Startup: showing saved data from {DATA_FILE} - not syncing.")
            return planner_html.render_html(
                data, completed, embedded=True, settings=settings,
                pinned=task_state.load_pinned_ids(ROOT), notes=task_state.load_notes(ROOT),
            )
        except Exception as exc:  # noqa: BLE001 - treat as missing
            print(f"Startup: couldn't use {DATA_FILE} ({exc}).")
    else:
        print(f"Startup: no saved data at {DATA_FILE}.")
    empty = {"todos": [], "days": [], "all_classes": [], "main_url": "", "generated_at": None}
    return planner_html.render_html(
        empty, [], embedded=True, settings=settings,
        pinned=task_state.load_pinned_ids(ROOT), notes=task_state.load_notes(ROOT),
    )


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
        html=load_cached_html(),  # no auto-sync
        js_api=api,
        width=980,
        height=780,
        min_size=(MIN_WIDTH, MIN_HEIGHT),
        frameless=True,  # frameless; page draws the title bar
        easy_drag=False,  # drag region = title bar only
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