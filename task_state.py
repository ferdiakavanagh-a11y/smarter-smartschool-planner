"""Checked-off task ids; kept apart from planner_data.json, which every sync overwrites."""

from __future__ import annotations

import json
from pathlib import Path


def _file_path(root: Path) -> Path:
    return root / "data" / "completed_tasks.json"


def load_completed_ids(root: Path) -> set[str]:
    path = _file_path(root)
    if not path.exists():
        return set()
    try:
        return set(json.loads(path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError):
        return set()


def save_completed_ids(root: Path, ids: set[str]) -> None:
    path = _file_path(root)
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(sorted(ids)), encoding="utf-8")


def set_task_done(root: Path, task_id: str, done: bool) -> set[str]:
    ids = load_completed_ids(root)
    if done:
        ids.add(task_id)
    else:
        ids.discard(task_id)
    save_completed_ids(root, ids)
    return ids


# UI settings

def _settings_path(root: Path) -> Path:
    return root / "data" / "ui_settings.json"


def load_settings(root: Path) -> dict:
    path = _settings_path(root)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def set_setting(root: Path, key: str, value) -> dict:
    settings = load_settings(root)
    settings[key] = value
    path = _settings_path(root)
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(settings), encoding="utf-8")
    return settings


# pins and notes (keyed by task id)

def _pinned_path(root: Path) -> Path:
    return root / "data" / "pinned_tasks.json"


def _notes_path(root: Path) -> Path:
    return root / "data" / "task_notes.json"


def load_pinned_ids(root: Path) -> list[str]:
    try:
        data = json.loads(_pinned_path(root).read_text(encoding="utf-8"))
        return [str(x) for x in data] if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def set_task_pinned(root: Path, task_id: str, pinned: bool) -> list[str]:
    ids = [i for i in load_pinned_ids(root) if i != task_id]
    if pinned:
        ids.append(task_id)
    path = _pinned_path(root)
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(ids), encoding="utf-8")
    return ids


def load_notes(root: Path) -> dict[str, str]:
    try:
        data = json.loads(_notes_path(root).read_text(encoding="utf-8"))
        return {str(k): str(v) for k, v in data.items()} if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def set_note(root: Path, task_id: str, text: str) -> dict[str, str]:
    notes = load_notes(root)
    text = (text or "").strip()
    if text:
        notes[task_id] = text[:5000]
    else:
        notes.pop(task_id, None)
    path = _notes_path(root)
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(notes, ensure_ascii=False), encoding="utf-8")
    return notes
