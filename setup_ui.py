"""
First-run setup window: saves secrets in Windows Credential Manager.

Used by desktop_app.py when credentials.yml is missing, or when the app is
started with --setup (the "Change credentials" shortcut does this).
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import date
from pathlib import Path

import credential_store
from process_lock import file_lock

PLACEHOLDER_MFA = "REPLACE_ME"  # what credentials.yml.example ships with

_DUTCH = {
    "Smartschool Planner - Setup": "Smartschool Planner - Verbinden",
    "Connect your Smartschool account": "Verbind je Smartschool-account",
    "Your details are protected by Windows Credential Manager.": "Windows Referentiebeheer bewaart je gegevens veilig.",
    "Username": "Gebruikersnaam",
    "Same as on the Smartschool website": "Dezelfde naam als op de Smartschool-website",
    "Password": "Wachtwoord",
    "School address": "Schooladres",
    "e.g. yourschool.smartschool.be": "Bijvoorbeeld jouwschool.smartschool.be",
    "Optional AI features": "Optionele AI-functies",
    "Security answer (optional)": "Beveiligingsantwoord (optioneel)",
    "Birthdate as YYYY-MM-DD (if login asks), or your 2FA secret": "Je geboortedatum als JJJJ-MM-DD (als Smartschool erom vraagt), of je 2FA-geheim",
    "Gemini API key (optional)": "Gemini API-sleutel (optioneel)",
    "Enables deadline detection - free at aistudio.google.com/apikey": "Voor datumcontrole met AI. Gratis via aistudio.google.com/apikey",
    "Cancel": "Annuleren", "Save": "Opslaan",
    "Missing info": "Er mist nog iets",
    "Username, password and school address are required.": "Vul je gebruikersnaam, wachtwoord en schooladres in.",
    "Security answer": "Beveiligingsantwoord",
    "Birthdate must be in YYYY-MM-DD format, e.g. 2008-05-14.": "Vul je geboortedatum in als JJJJ-MM-DD, bijvoorbeeld 2008-05-14.",
    "Login details unavailable": "Je aanmeldgegevens zijn niet beschikbaar",
    "Saved login details could not be opened. Enter them again to replace them.": "Je opgeslagen aanmeldgegevens konden niet worden geopend. Vul ze opnieuw in om ze te vervangen.",
    "Repair login configuration": "Aanmeldgegevens herstellen",
    "Replace the damaged configuration? An encrypted recovery copy will be kept on this computer.": "Wil je de beschadigde instellingen vervangen? Er blijft een versleutelde herstelkopie op deze computer staan.",
    "Could not save": "Opslaan lukt niet",
    "Windows could not securely save your details. Existing details were kept. Check Credential Manager and try again.": "Windows kon je gegevens niet veilig opslaan. Je bestaande gegevens blijven bewaard. Kijk even bij Referentiebeheer en probeer het opnieuw.",
    "Login window already open": "Het aanmeldvenster staat al open",
    "Close the existing login window before opening another one.": "Sluit eerst het andere aanmeldvenster.",
    "Show password": "Toon je wachtwoord", "Hide password": "Verberg je wachtwoord",
    "Show security answer": "Toon je beveiligingsantwoord", "Hide security answer": "Verberg je beveiligingsantwoord",
    "Show Gemini API key": "Toon je Gemini API-sleutel", "Hide Gemini API key": "Verberg je Gemini API-sleutel",
}


def _setup_text(text: str, language: str) -> str:
    return _DUTCH.get(text, text) if language == "nl" else text


def clean_url(value: str) -> str:
    v = value.strip()
    for prefix in ("https://", "http://"):
        if v.lower().startswith(prefix):
            v = v[len(prefix):]
    return v.split("/")[0].strip()


def normalize_security(value: str):
    """Birthdate answers must be YYYY-MM-DD. Accepts DD-MM-YYYY, DD/MM/YYYY,
    YYYY/MM/DD, YYYYMMDD and converts. Anything that isn't date-like (e.g. a
    2FA secret) is kept as is. Returns (value, error_message_or_None)."""
    v = value.strip()
    if not v or any(c not in "0123456789-./" for c in v):
        return v, None
    bad = ("Birthdate must be in YYYY-MM-DD format, e.g. 2008-05-14.")
    if v.isdigit() and len(v) == 8:
        y, m, d = v[:4], v[4:6], v[6:]
    else:
        parts = v.replace(".", "-").replace("/", "-").split("-")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            return v, bad
        a, m, c = parts
        if len(a) == 4 and len(c) <= 2:
            y, d = a, c
        elif len(c) == 4 and len(a) <= 2:
            y, d = c, a
        else:
            return v, bad
    try:
        normalized = date(int(y), int(m), int(d)).isoformat()
    except ValueError:
        return v, bad
    return normalized, None


def load_existing(path: Path) -> dict:
    return credential_store.load_for_setup(path)


def restrict_permissions(path: Path) -> None:
    """Owner-only access. Best effort; never blocks saving."""
    try:
        if os.name == "nt":
            user = os.environ.get("USERNAME", "")
            if user:
                subprocess.run(
                    ["icacls", str(path), "/inheritance:r", "/grant:r", f"{user}:F"],
                    capture_output=True,
                    creationflags=0x08000000,  # CREATE_NO_WINDOW
                    check=False,
                )
        else:
            path.chmod(0o600)
    except Exception:  # noqa: BLE001
        pass


@credential_store.credential_transaction
def write_credentials(path: Path, username, password, main_url, mfa="", gemini_key="", recover=False) -> None:
    try:
        data = credential_store.read_config(path)
    except credential_store.CredentialError:
        if not recover:
            raise
        from windows_security import protect, atomic_bytes
        atomic_bytes(path.with_suffix('.recovery.bin'), protect(path.read_bytes()))
        data = {}
    data.update(
        {
            "username": username.strip(),
            "password": password,
            "main_url": clean_url(main_url),
            "mfa": mfa.strip() or PLACEHOLDER_MFA,
            "gemini_api_key": gemini_key.strip(),
        }
    )
    data.setdefault("planner_detail_url", "")
    credential_store.save_credentials(path, data)
    restrict_permissions(path)


def run_setup(path: Path) -> bool:
    """Show the form. Returns True if credentials were saved."""
    try:
        with file_lock(path.parent / 'data' / '.setup.lock', timeout=0):
            return _run_setup(path)
    except TimeoutError:
        from tkinter import messagebox
        import task_state
        language = task_state.load_settings(path.parent).get('language', 'en')
        messagebox.showinfo(_setup_text('Login window already open', language), _setup_text('Close the existing login window before opening another one.', language))
        return False


def _run_setup(path: Path) -> bool:
    import tkinter as tk
    from tkinter import messagebox, ttk

    load_error = False
    try:
        existing = load_existing(path)
    except (OSError, credential_store.CredentialError):
        existing = {}
        load_error = True
    saved = {"ok": False}

    root = tk.Tk()
    root.resizable(False, False)
    import task_state
    appearance = task_state.load_settings(path.parent)
    tr = lambda value: _setup_text(value, appearance.get('language', 'en'))
    root.title(tr("Smartschool Planner - Setup"))
    dark = appearance.get("scheme") == "dark"
    smartschool = appearance.get("renderingMode") == "performance"
    background = "#1E2023" if dark else "#F4F4F4"
    foreground = "#F3F3F3" if dark else "#292929"
    accent = ("#F2A48D" if dark else "#B7503D") if smartschool else "#2F76B8"
    text_size = appearance.get("textSize", 1)
    if type(text_size) not in (int, float) or not .9 <= text_size <= 1.35:
        text_size = 1
    root.configure(background=background)
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(".", background=background, foreground=foreground, font=("Segoe UI", round(10 * text_size)))
    style.configure("TEntry", fieldbackground="#282B2E" if dark else "white", foreground=foreground, padding=5)
    style.configure("TButton", padding=(12, 6))
    style.configure("Reveal.TButton", padding=(6, 5))
    style.map("TButton", background=[("pressed", "#494E53" if dark else "#DDDDDD"), ("active", "#34373A" if dark else "#E6E7E8")], foreground=[("!disabled", foreground)], bordercolor=[("focus", accent)])
    style.configure("Accent.TButton", background=accent, foreground="#24170F" if dark and smartschool else "white")
    style.map("Accent.TButton", background=[("active", "#943D2C" if smartschool else "#94491F")], foreground=[("active", "white")])
    if load_error:
        messagebox.showwarning(tr('Login details unavailable'), tr('Saved login details could not be opened. Enter them again to replace them.'), parent=root)
    try:
        icon = Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "assets" / "icon.ico"
        if icon.exists():
            root.iconbitmap(str(icon))
    except Exception:  # noqa: BLE001
        pass

    frm = ttk.Frame(root, padding=18)
    frm.grid()

    ttk.Label(frm, text=tr("Connect your Smartschool account"), font=("Segoe UI", round(13 * text_size), "bold")).grid(
        row=0, column=0, columnspan=2, sticky="w", pady=(0, 4)
    )
    ttk.Label(
        frm,
        text=tr("Your details are protected by Windows Credential Manager."),
        foreground=foreground,
    ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 12))

    assets = Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "assets" / "setup"
    size = 32 if text_size > 1.15 else 24
    icons = {}
    for action in ('show', 'hide'):
        try:
            icons[action] = tk.PhotoImage(master=root, file=str(assets / f"eye-{action}-{'dark' if dark else 'light'}-{size}.png"))
        except tk.TclError:
            pass
    protected = []

    def field(row, label, hint, value="", show=None, key="", secret_label=""):
        ttk.Label(frm, text=tr(label)).grid(row=row * 2 + 2, column=0, sticky="w", pady=(6, 0), padx=(0, 12))
        var = tk.StringVar(value=value)
        input_row = ttk.Frame(frm)
        input_row.grid(row=row * 2 + 2, column=1, sticky="ew", pady=(6, 0))
        input_row.columnconfigure(0, weight=1)
        entry = ttk.Entry(input_row, name=key or f"field{row}", textvariable=var, width=38, show=show, font=("Segoe UI", round(10 * text_size)))
        entry.grid(row=0, column=0, sticky="ew")
        if show:
            button = ttk.Button(input_row, name=f"reveal_{key}", text=tr(f"Show {secret_label}"), image=icons.get('show', ''), width=3 if len(icons)==2 else None, style="Reveal.TButton", takefocus=True)
            button.grid(row=0, column=1, padx=(6, 0))
            def mask(masked=True):
                entry.configure(show='*' if masked else '')
                button.configure(text=tr(f"Show {secret_label}" if masked else f"Hide {secret_label}"), image=icons.get('show' if masked else 'hide', ''))
            def toggle(): mask(not entry.cget('show'))
            button.configure(command=toggle)
            def keyboard_toggle(_event):
                toggle()
                return 'break'
            button.bind('<Return>', keyboard_toggle)
            protected.append(mask)
        ttk.Label(frm, text=tr(hint), foreground=foreground, font=("Segoe UI", round(8 * text_size)), wraplength=round(300 * text_size)).grid(
            row=row * 2 + 3, column=1, sticky="w"
        )
        return var

    mfa_old = str(existing.get("mfa", ""))
    v_user = field(0, "Username", "Same as on the Smartschool website", str(existing.get("username", "")))
    v_pass = field(1, "Password", "", str(existing.get("password", "")), show="*", key="password", secret_label="password")
    v_url = field(2, "School address", "e.g. yourschool.smartschool.be", str(existing.get("main_url", "")))
    v_mfa = field(
        3,
        "Security answer (optional)",
        "Birthdate as YYYY-MM-DD (if login asks), or your 2FA secret",
        "" if mfa_old == PLACEHOLDER_MFA else mfa_old,
        show="*",
        key="security", secret_label="security answer",
    )
    ttk.Separator(frm).grid(row=10, column=0, columnspan=2, sticky="ew", pady=(10, 4))
    ttk.Label(frm, text=tr("Optional AI features"), font=("Segoe UI", round(10 * text_size), "bold")).grid(row=11, column=0, columnspan=2, sticky="w")
    v_key = field(
        5,
        "Gemini API key (optional)",
        "Enables deadline detection - free at aistudio.google.com/apikey",
        str(existing.get("gemini_api_key", "") or ""),
        show="*",
        key="gemini", secret_label="Gemini API key",
    )

    def mask_all():
        for mask in protected: mask()

    def mask_if_inactive():
        try:
            if root.focus_displayof() is None: mask_all()
        except tk.TclError:
            pass
    root.bind('<FocusOut>', lambda _event: root.after_idle(mask_if_inactive), add='+')
    root.bind('<Unmap>', lambda event: mask_all() if event.widget is root else None, add='+')

    def on_save():
        mask_all()
        if not v_user.get().strip() or not v_pass.get() or not clean_url(v_url.get()):
            messagebox.showerror(tr("Missing info"), tr("Username, password and school address are required."), parent=root)
            return
        mfa_value, err = normalize_security(v_mfa.get())
        if err:
            messagebox.showerror(tr("Security answer"), tr(err), parent=root)
            return
        try:
            recover = False
            try:
                credential_store.read_config(path)
            except credential_store.CredentialError:
                recover = messagebox.askyesno(tr('Repair login configuration'), tr('Replace the damaged configuration? An encrypted recovery copy will be kept on this computer.'), parent=root)
                if not recover:
                    return
            write_credentials(path, v_user.get(), v_pass.get(), v_url.get(), mfa_value, v_key.get(), recover=recover)
        except Exception:  # Never include secret-bearing exception payloads in UI or logs.
            messagebox.showerror(tr("Could not save"), tr("Windows could not securely save your details. Existing details were kept. Check Credential Manager and try again."), parent=root)
            return
        saved["ok"] = True
        root.destroy()

    btns = ttk.Frame(frm)
    btns.grid(row=14, column=0, columnspan=2, sticky="e", pady=(16, 0))
    ttk.Button(btns, name="cancel", text=tr("Cancel"), command=root.destroy).grid(row=0, column=0, padx=6)
    ttk.Button(btns, name="save", text=tr("Save"), style="Accent.TButton", command=on_save).grid(row=0, column=1)
    root.bind("<Return>", lambda _e: on_save())

    root.update_idletasks()
    w, h = root.winfo_reqwidth(), root.winfo_reqheight()
    root.geometry(f"+{(root.winfo_screenwidth() - w) // 2}+{(root.winfo_screenheight() - h) // 3}")
    root.mainloop()
    return saved["ok"]
