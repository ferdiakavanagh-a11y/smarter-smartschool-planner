"""User-scoped Windows vault storage; YAML contains only configuration and a reference."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import tempfile
import threading
import uuid

import yaml

SECRET_FIELDS = ('username', 'password', 'mfa', 'gemini_api_key')
_lock = threading.RLock()


class CredentialError(ValueError):
    """Safe to display: never contains credential values."""


class _Credential(ctypes.Structure):
    _fields_ = [('Flags', wintypes.DWORD), ('Type', wintypes.DWORD),
                ('TargetName', wintypes.LPWSTR), ('Comment', wintypes.LPWSTR),
                ('LastWritten', wintypes.FILETIME), ('CredentialBlobSize', wintypes.DWORD),
                ('CredentialBlob', ctypes.POINTER(ctypes.c_ubyte)), ('Persist', wintypes.DWORD),
                ('AttributeCount', wintypes.DWORD), ('Attributes', ctypes.c_void_p),
                ('TargetAlias', wintypes.LPWSTR), ('UserName', wintypes.LPWSTR)]


def _api():
    if os.name != 'nt':
        raise CredentialError('Secure credential storage requires Windows. No plaintext fallback is used.')
    api = ctypes.WinDLL('Advapi32.dll', use_last_error=True)
    pointer = ctypes.POINTER(_Credential)
    api.CredWriteW.argtypes = [pointer, wintypes.DWORD]
    api.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(pointer)]
    api.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
    api.CredEnumerateW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(ctypes.POINTER(pointer))]
    for name in ('CredWriteW', 'CredReadW', 'CredDeleteW', 'CredEnumerateW'):
        getattr(api, name).restype = wintypes.BOOL
    api.CredFree.argtypes = [ctypes.c_void_p]
    api.CredFree.restype = None
    return api


def _prefix(path: Path) -> str:
    identity = str(path.resolve()).casefold().encode('utf-8')
    return 'SmartschoolPlanner/' + hashlib.sha256(identity).hexdigest()[:24] + '/'


def _read(target: str) -> dict:
    api = _api()
    pointer = ctypes.POINTER(_Credential)()
    if not api.CredReadW(target, 1, 0, ctypes.byref(pointer)):
        raise CredentialError('Saved login details are unavailable. Use Change login info to enter them again.')
    try:
        raw = ctypes.string_at(pointer.contents.CredentialBlob, pointer.contents.CredentialBlobSize)
        data = json.loads(raw.decode('utf-8'))
        if not isinstance(data, dict) or set(data) != set(SECRET_FIELDS) or not all(isinstance(v, str) for v in data.values()):
            raise ValueError()
        return data
    except (ValueError, UnicodeError):
        raise CredentialError('Saved login details could not be read. Use Change login info.') from None
    finally:
        api.CredFree(pointer)


def _delete(target: str) -> None:
    api = _api()
    if not api.CredDeleteW(target, 1, 0) and ctypes.get_last_error() != 1168:
        raise CredentialError('Windows could not remove saved login details.')


def read_config(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding='utf-8')) or {}
    except FileNotFoundError:
        return {}
    except yaml.YAMLError:
        raise CredentialError('The login configuration is invalid. Use Change login info.') from None
    if not isinstance(data, dict):
        raise CredentialError('The login configuration is invalid. Use Change login info.')
    return data


def save_credentials(path: Path, data: dict) -> None:
    """Commit a verified new vault entry before atomically replacing the YAML."""
    with _lock:
        config = {k: v for k, v in data.items() if k not in SECRET_FIELDS and k != 'vault_target'}
        secrets = {k: str(data.get(k) or '') for k in SECRET_FIELDS}
        blob = json.dumps(secrets, ensure_ascii=False).encode('utf-8')
        if len(blob) > 2560:
            raise CredentialError('Login details exceed the Windows credential storage limit.')
        target = _prefix(path) + uuid.uuid4().hex
        api = _api()
        buffer = (ctypes.c_ubyte * len(blob)).from_buffer_copy(blob)
        record = _Credential(Type=1, TargetName=target, CredentialBlobSize=len(blob),
                             CredentialBlob=buffer, Persist=2, UserName='Smartschool Planner')
        try:
            written = api.CredWriteW(ctypes.byref(record), 0)
        finally:
            ctypes.memset(buffer, 0, len(buffer))
        if not written:
            raise CredentialError('Windows Credential Manager could not save your details. Existing details were kept.')
        committed = False
        temporary = None
        try:
            if _read(target) != secrets:
                raise CredentialError('Windows could not verify the saved login details.')
            config['vault_target'] = target
            path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as file:
                temporary = Path(file.name)
                file.write(yaml.safe_dump(config, allow_unicode=True, sort_keys=False))
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary, path)
            committed = True
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
            if not committed:
                _delete(target)
        old = data.get('vault_target')
        if isinstance(old, str) and old.startswith(_prefix(path)) and old != target:
            try:
                _delete(old)
            except CredentialError:
                pass  # Uninstall also removes orphaned entries belonging to this installation.


def load_credentials(path: Path) -> dict:
    with _lock:
        config = read_config(path)
        target = config.get('vault_target')
        if target:
            if not isinstance(target, str) or not target.startswith(_prefix(path)):
                raise CredentialError('Login details belong to another installation. Use Change login info.')
            data = {**config, **_read(target)}
            if any(k in config for k in SECRET_FIELDS):
                save_credentials(path, data)
            return data
        if any(k in config for k in SECRET_FIELDS):
            save_credentials(path, config)
        return config


def smartschool_credentials(path: Path):
    from smartschool import AppCredentials
    data = load_credentials(path)
    return AppCredentials(username=data.get('username', ''), password=data.get('password', ''),
                          main_url=data.get('main_url', ''), mfa=data.get('mfa') or 'REPLACE_ME',
                          other_info={k: v for k, v in data.items() if k not in ('username', 'password', 'main_url', 'mfa', 'vault_target')})


def clear_credentials(path: Path) -> None:
    """Delete only this installation's generic entries, including interrupted saves."""
    api = _api()
    count = wintypes.DWORD()
    entries = ctypes.POINTER(ctypes.POINTER(_Credential))()
    if not api.CredEnumerateW(_prefix(path) + '*', 0, ctypes.byref(count), ctypes.byref(entries)):
        if ctypes.get_last_error() == 1168:
            return
        raise CredentialError('Windows could not list the saved login details for removal.')
    try:
        targets = [entries[i].contents.TargetName for i in range(count.value) if entries[i].contents.Type == 1]
    finally:
        api.CredFree(entries)
    for target in targets:
        _delete(target)
