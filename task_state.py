"""Checked-off task ids; kept apart from planner_data.json, which every sync overwrites."""

from __future__ import annotations

import json
import os
import tempfile
from functools import wraps
from pathlib import Path

from process_lock import file_lock


def state_write(function):
    @wraps(function)
    def wrapped(root: Path, *args, **kwargs):
        with file_lock(root / 'data' / '.state.lock'):
            return function(root, *args, **kwargs)
    return wrapped


def _atomic_json(path: Path, data) -> None:
    path.parent.mkdir(exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as file:
            temporary = Path(file.name)
            json.dump(data, file, ensure_ascii=False)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _file_path(root: Path) -> Path:
    return root / "data" / "completed_tasks.json"


def _load_json(path: Path, container_type, strict: bool):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, container_type) or (isinstance(data, list) and not all(isinstance(x, str) for x in data)):
            raise ValueError('Invalid saved state')
        return data
    except FileNotFoundError:
        return container_type()
    except (ValueError, OSError):
        if strict:
            raise ValueError(f'Could not read {path.name}. Existing data was kept.') from None
        return container_type()


def load_completed_ids(root: Path, *, strict: bool = False) -> set[str]:
    return set(_load_json(_file_path(root), list, strict))


@state_write
def save_completed_ids(root: Path, ids: set[str]) -> None:
    _atomic_json(_file_path(root), sorted(ids))


@state_write
def set_task_done(root: Path, task_id: str, done: bool) -> set[str]:
    ids = load_completed_ids(root, strict=True)
    if done:
        ids.add(task_id)
    else:
        ids.discard(task_id)
    save_completed_ids(root, ids)
    return ids


# UI settings

def _settings_path(root: Path) -> Path:
    return root / "data" / "ui_settings.json"


def load_settings(root: Path, *, strict: bool = False) -> dict:
    return _load_json(_settings_path(root), dict, strict)


def date_checker_mode(root: Path, gemini_key) -> str:
    if not str(gemini_key or '').strip():
        return 'local'
    return 'local' if load_settings(root).get('dateChecker') == 'local' else 'gemini'


def date_checker_state(root: Path) -> dict:
    import credential_store
    credentials = credential_store.load_credentials(root / 'credentials.yml')
    key = credentials.get('gemini_api_key')
    return {'mode': date_checker_mode(root, key), 'geminiAvailable': bool(str(key or '').strip())}


@state_write
def set_setting(root: Path, key: str, value) -> dict:
    if key == "renderingMode" and value not in ("performance", "fancy"):
        raise ValueError("Unknown rendering mode")
    if key == 'dateChecker':
        if value not in ('local', 'gemini'):
            raise ValueError('Unknown date checker')
        if value == 'gemini' and not date_checker_state(root)['geminiAvailable']:
            raise ValueError('A Gemini API key is required')
    settings = load_settings(root, strict=True)
    settings[key] = value
    _atomic_json(_settings_path(root), settings)
    return settings


def rendering_choice_pending(root: Path) -> bool:
    return (root / "data" / "rendering_choice_pending").exists()


@state_write
def save_appearance_settings(root: Path, values: dict) -> dict:
    """Commit native preferences together, preserving unrelated settings and read state."""
    allowed = {'renderingMode', 'style', 'scheme', 'glassLevel', 'distortion', 'textSize',
               'wallpaperIndex', 'reducedMotion', 'animatedBackground', 'highContrast'}
    if set(values) - allowed:
        raise ValueError('Unknown appearance setting')
    settings = load_settings(root, strict=True)
    settings.update(values)
    settings['qmlVersion'] = 1
    _atomic_json(_settings_path(root), settings)
    return settings


# pins and notes (keyed by task id)

def _pinned_path(root: Path) -> Path:
    return root / "data" / "pinned_tasks.json"


def _notes_path(root: Path) -> Path:
    return root / "data" / "task_notes.json"


def load_pinned_ids(root: Path, *, strict: bool = False) -> list[str]:
    return _load_json(_pinned_path(root), list, strict)


@state_write
def set_task_pinned(root: Path, task_id: str, pinned: bool) -> list[str]:
    ids = [i for i in load_pinned_ids(root, strict=True) if i != task_id]
    if pinned:
        ids.append(task_id)
    path = _pinned_path(root)
    _atomic_json(path, ids)
    return ids


def load_notes(root: Path, *, strict: bool = False) -> dict[str, str]:
    data = _load_json(_notes_path(root), dict, strict)
    if strict and any(not isinstance(value, str) for value in data.values()):
        raise ValueError('Could not read task_notes.json. Existing data was kept.')
    return {str(k): str(v) for k, v in data.items()}


@state_write
def set_note(root: Path, task_id: str, text: str) -> dict[str, str]:
    notes = load_notes(root, strict=True)
    text = (text or "").strip()
    if len(text) > 5000:
        raise ValueError('Notes can contain up to 5000 characters. The original note was kept.')
    if text:
        notes[task_id] = text
    else:
        notes.pop(task_id, None)
    path = _notes_path(root)
    _atomic_json(path, notes)
    return notes


@state_write
def migrate_task_ids(root: Path, aliases: dict) -> None:
    """Copy state to merged IDs; retain originals so interrupted migrations are recoverable."""
    aliases = {old: new for old, new in aliases.items() if old != new}
    if not aliases:
        return
    completed, pinned, notes = load_completed_ids(root, strict=True), load_pinned_ids(root, strict=True), load_notes(root, strict=True)
    for old, new in aliases.items():
        if old in completed:
            completed.add(new)
        if old in pinned and new not in pinned:
            pinned.append(new)
        if notes.get(old) and notes[old] not in notes.get(new, ''):
            notes[new] = (notes[new] + '\n\n' + notes[old]) if notes.get(new) else notes[old]
    _atomic_json(_file_path(root), sorted(completed))
    _atomic_json(_pinned_path(root), pinned)
    _atomic_json(_notes_path(root), notes)
