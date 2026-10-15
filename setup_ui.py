"""
First-run setup window: saves secrets in Windows Credential Manager.

Used by desktop_app.py when credentials.yml is missing, or when the app is
started with --setup (the "Change credentials" shortcut does this).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import credential_store

PLACEHOLDER_MFA = "REPLACE_ME"  # what credentials.yml.example ships with


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
    if not (1 <= int(m) <= 12 and 1 <= int(d) <= 31):
        return v, bad
    return f"{y}-{int(m):02d}-{int(d):02d}", None


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
    root.title("Smartschool Planner - Setup")
    root.resizable(False, False)
    if load_error:
        messagebox.showwarning('Login details unavailable', 'Saved login details could not be opened. Enter them again to replace them.', parent=root)
    try:
        icon = Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "assets" / "icon.ico"
        if icon.exists():
            root.iconbitmap(str(icon))
    except Exception:  # noqa: BLE001
        pass

    frm = ttk.Frame(root, padding=18)
    frm.grid()

    ttk.Label(frm, text="Connect your Smartschool account", font=("Segoe UI", 13, "bold")).grid(
        row=0, column=0, columnspan=2, sticky="w", pady=(0, 4)
    )
    ttk.Label(
        frm,
        text="Your details are protected by Windows Credential Manager.",
        foreground="#555",
    ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 12))

    def field(row, label, hint, value="", show=None):
        ttk.Label(frm, text=label).grid(row=row * 2 + 2, column=0, sticky="w", pady=(6, 0))
        var = tk.StringVar(value=value)
        ttk.Entry(frm, textvariable=var, width=38, show=show).grid(row=row * 2 + 2, column=1, pady=(6, 0))
        ttk.Label(frm, text=hint, foreground="#777", font=("Segoe UI", 8)).grid(
            row=row * 2 + 3, column=1, sticky="w"
        )
        return var

    mfa_old = str(existing.get("mfa", ""))
    v_user = field(0, "Username", "Same as on the Smartschool website", str(existing.get("username", "")))
    v_pass = field(1, "Password", "", str(existing.get("password", "")), show="*")
    v_url = field(2, "School address", "e.g. yourschool.smartschool.be", str(existing.get("main_url", "")))
    v_mfa = field(
        3,
        "Security answer (optional)",
        "Birthdate as YYYY-MM-DD (if login asks), or your 2FA secret",
        "" if mfa_old == PLACEHOLDER_MFA else mfa_old,
        show="*",
    )
    v_key = field(
        4,
        "Gemini API key (optional)",
        "Enables deadline detection - free at aistudio.google.com/apikey",
        str(existing.get("gemini_api_key", "") or ""),
        show="*",
    )

    def on_save():
        if not v_user.get().strip() or not v_pass.get() or not clean_url(v_url.get()):
            messagebox.showerror("Missing info", "Username, password and school address are required.")
            return
        mfa_value, err = normalize_security(v_mfa.get())
        if err:
            messagebox.showerror("Security answer", err)
            return
        try:
            recover = False
            try:
                credential_store.read_config(path)
            except credential_store.CredentialError:
                recover = messagebox.askyesno('Repair login configuration', 'Replace the damaged configuration? An encrypted recovery copy will be kept on this computer.', parent=root)
                if not recover:
                    return
            write_credentials(path, v_user.get(), v_pass.get(), v_url.get(), mfa_value, v_key.get(), recover=recover)
        except Exception:  # Never include secret-bearing exception payloads in UI or logs.
            messagebox.showerror("Could not save", "Windows could not securely save your details. Existing details were kept. Check Credential Manager and try again.")
            return
        saved["ok"] = True
        root.destroy()

    btns = ttk.Frame(frm)
    btns.grid(row=14, column=0, columnspan=2, sticky="e", pady=(16, 0))
    ttk.Button(btns, text="Cancel", command=root.destroy).grid(row=0, column=0, padx=6)
    ttk.Button(btns, text="Save", command=on_save).grid(row=0, column=1)
    root.bind("<Return>", lambda _e: on_save())

    root.update_idletasks()
    w, h = root.winfo_reqwidth(), root.winfo_reqheight()
    root.geometry(f"+{(root.winfo_screenwidth() - w) // 2}+{(root.winfo_screenheight() - h) // 3}")
    root.mainloop()
    return saved["ok"]
