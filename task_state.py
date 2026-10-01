"""
Tracks which tasks you've checked off as done. Kept separate from
data/planner_data.json because that file gets fully overwritten on every
sync - completion state needs to survive that.
"""

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


# ---- UI settings (appearance, glass level, reduce motion) ----

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
