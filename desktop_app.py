"""Native desktop window for the planner UI (exe entry point). Run: python desktop_app.py"""

from __future__ import annotations

import sys
import threading
import time
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
import os  # noqa: E402
import subprocess  # noqa: E402
from datetime import datetime  # noqa: E402

import app_errors  # noqa: E402
import planner_html  # noqa: E402
import sync  # noqa: E402
import task_state  # noqa: E402
import updater  # noqa: E402
import webview  # noqa: E402
from version import __version__  # noqa: E402
from webview.window import FixPoint  # noqa: E402

MIN_WIDTH, MIN_HEIGHT = 760, 560
DATA_FILE = ROOT / "data" / "planner_data.json"
CREDS_FILE = ROOT / "credentials.yml"
LOG_FILE = ROOT / "error.log"


def log_error(info: dict) -> None:
    """Keep a local copy of the last problems (error.log next to the app). Never sent anywhere."""
    try:
        if LOG_FILE.exists() and LOG_FILE.stat().st_size > 200_000:
            LOG_FILE.write_text("", encoding="utf-8")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {info.get('kind')}: {info.get('title')} - {info.get('message')}\n")
            if info.get("details"):
                f.write(str(info["details"])[-4000:] + "\n")
            f.write("\n")
    except Exception:  # noqa: BLE001 - logging must never break the app
        pass


def show_error(window, info: dict) -> None:
    """Overlay the error on the current page (keeps the last data visible behind it)."""
    try:
        window.evaluate_js("showError(" + json.dumps(info) + ")")
    except Exception:  # noqa: BLE001 - page not ready: fall back to a full error page
        window.load_html(planner_html.render_error(info, task_state.load_settings(ROOT)))


_UPDATE_POPUP_JS = r"""(function(){
if(document.getElementById('upd-banner'))return;
var o=document.createElement('div');o.id='upd-banner';
o.style.cssText="position:fixed;inset:0;z-index:2147483000;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,.55);font:14px/1.45 system-ui,Segoe UI,sans-serif";
o.innerHTML='<div style="width:min(420px,90vw);padding:22px 24px;border-radius:14px;background:#1f2430;color:#fff;box-shadow:0 12px 40px rgba(0,0,0,.45);border:1px solid rgba(255,255,255,.14)">'
+'<div style="font-size:17px;font-weight:700;margin-bottom:8px">Update available</div>'
+'<div id="upd-text" style="margin-bottom:6px"></div>'
+'<div id="upd-ask" style="opacity:.75;margin-bottom:16px">Do you want to update now? The app will restart.</div>'
+'<div id="upd-btns" style="display:flex;gap:10px;justify-content:flex-end">'
+'<button id="upd-no" style="padding:9px 18px;border:1px solid rgba(255,255,255,.28);border-radius:8px;background:transparent;color:#fff;font:inherit;cursor:pointer">No</button>'
+'<button id="upd-yes" style="padding:9px 18px;border:0;border-radius:8px;background:#6c8cff;color:#fff;font:inherit;font-weight:600;cursor:pointer">Yes</button>'
+'</div></div>';
document.body.appendChild(o);
var t=document.getElementById('upd-text'),a=document.getElementById('upd-ask'),b=document.getElementById('upd-btns');
var yes=document.getElementById('upd-yes'),no=document.getElementById('upd-no');
t.textContent=__TEXT__;
if(__BUSY__){b.style.display='none';a.style.display='none';}
yes.onclick=function(){b.style.display='none';a.style.display='none';pywebview.api.install_update();};
no.onclick=function(){pywebview.api.dismiss_update();o.remove();};
window.__updStatus=function(x,failed){t.textContent=x;b.style.display=failed?'flex':'none';a.style.display='none';yes.textContent=failed?'Try again':'Yes';no.textContent=failed?'Close':'No';};
})()
"""


class Api:
    """Methods callable from the page JS. Never store the window as a public attribute
    (pywebview's bridge recurses into it forever); use a leading underscore."""

    def __init__(self):
        self._window = None
        self._maximized = False
        self._update = None  # info about a newer release, once found
        self._update_dismissed = False
        self._update_busy = False
        self._update_text = ""

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

    def open_setup(self):
        """Open the login-details window (a separate process, so the page stays responsive)."""
        threading.Thread(target=self._run_setup, daemon=True).start()
        return True

    def _run_setup(self):
        before = CREDS_FILE.stat().st_mtime if CREDS_FILE.exists() else None
        if getattr(sys, "frozen", False):
            cmd = [sys.executable, "--setup-only"]
        else:
            cmd = [sys.executable, str(Path(__file__).resolve()), "--setup-only"]
        env = dict(os.environ, PYINSTALLER_RESET_ENVIRONMENT="1")  # start a fresh, independent copy
        try:
            subprocess.run(cmd, env=env, check=False)
        except Exception as exc:  # noqa: BLE001
            log_error({"kind": "config", "title": "Could not open login window", "message": str(exc), "details": traceback.format_exc()})
        after = CREDS_FILE.stat().st_mtime if CREDS_FILE.exists() else None
        if after != before:
            do_sync_and_render(self._window)  # new details saved: try again straight away
        else:
            try:
                self._window.evaluate_js("hideState()")
            except Exception:  # noqa: BLE001
                pass

    # auto-update (the page's banner buttons call install_update / dismiss_update)
    def install_update(self):
        threading.Thread(target=self._do_update, daemon=True).start()
        return True

    def dismiss_update(self):
        self._update_dismissed = True
        return True

    def _start_update_check(self):
        threading.Thread(target=self._check_for_update, daemon=True).start()

    def _check_for_update(self):
        if not getattr(sys, "frozen", False) and not os.environ.get("SSP_UPDATE_TEST"):
            return  # only the installed exe updates itself
        try:
            info = updater.check_for_update(__version__)
        except Exception as exc:  # noqa: BLE001 - offline, rate limited...: never bother the user
            log_error({"kind": "info", "title": "Update check failed", "message": str(exc), "details": ""})
            return
        if not info:
            return
        self._update = info
        self._update_text = f"Version {info['version']} is available (you have {__version__})."
        log_error({"kind": "info", "title": "Update available", "message": info["version"], "details": ""})
        while not self._update_dismissed:  # re-add the banner whenever the page gets reloaded
            try:
                if not self._window.evaluate_js("!!document.getElementById('upd-banner')"):
                    self._window.evaluate_js(self._banner_js())
            except Exception:  # noqa: BLE001 - page mid-load
                pass
            time.sleep(2)

    def _banner_js(self) -> str:
        # centred pop-up over a dimmed page: "Update now?" Yes / No
        return _UPDATE_POPUP_JS.replace("__TEXT__", json.dumps(self._update_text)).replace(
            "__BUSY__", "true" if self._update_busy else "false"
        )

    def _banner_status(self, text: str, failed: bool = False) -> None:
        self._update_text = text
        try:
            self._window.evaluate_js(f"window.__updStatus&&window.__updStatus({json.dumps(text)},{'true' if failed else 'false'})")
        except Exception:  # noqa: BLE001
            pass

    def _do_update(self):
        if not self._update or self._update_busy:
            return
        self._update_busy = True
        try:
            self._banner_status("Downloading update...")
            last = [-1]

            def progress(done, total):
                pct = done * 100 // total if total else 0
                if pct != last[0] and total:
                    last[0] = pct
                    self._banner_status(f"Downloading update... {pct}%")

            path = updater.download_and_verify(self._update, progress)
            self._banner_status("Installing... the app will restart.")
            updater.launch_installer(path)
            time.sleep(1.5)
            self._window.destroy()  # the installer replaces the exe and starts the new version
        except Exception as exc:  # noqa: BLE001
            self._update_busy = False
            log_error({"kind": "update", "title": "Update failed", "message": str(exc), "details": traceback.format_exc()})
            self._banner_status("The update didn't work. Your app is unchanged.", failed=True)

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
            show_error(
                window,
                {
                    "kind": "config",
                    "title": "Login details missing",
                    "message": "No saved Smartschool login details were found.",
                    "hint": "Click Change login details to enter them.",
                    "details": "",
                },
            )
            return

        data = sync.run(days_back=10, days_ahead=21)
        completed = task_state.load_completed_ids(ROOT)
        html = planner_html.render_html(
            data, completed, embedded=True, settings=task_state.load_settings(ROOT),
            pinned=task_state.load_pinned_ids(ROOT), notes=task_state.load_notes(ROOT),
        )
        window.load_html(html)
    except Exception as exc:  # noqa: BLE001 - show a friendly error in-window
        info = app_errors.explain(exc, app_errors.read_main_url(CREDS_FILE))
        log_error(info)
        show_error(window, info)


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
    if "--setup-only" in sys.argv:  # helper mode: just the login-details window, then exit
        import setup_ui  # noqa: PLC0415

        setup_ui.run_setup(CREDS_FILE)
        return
    log_error({"kind": "info", "title": "App started", "message": f"version={__version__} folder={ROOT} exe={'yes' if getattr(sys, 'frozen', False) else 'no (python)'}"})
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
    window.events.shown += api._start_update_check
    window.events.maximized += api._on_maximized
    window.events.restored += api._on_restored
    if just_set_up:
        window.events.shown += api.sync_now  # first sync right after saving credentials
    webview.start()


if __name__ == "__main__":
    main()