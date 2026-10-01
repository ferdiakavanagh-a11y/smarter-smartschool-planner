"""
after running this you will find the html in the folder.

this is only for testing really, main app is built via the bat file.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def get_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


ROOT = get_root()
sys.path.insert(0, str(ROOT))

import planner_html  # noqa: E402

DATA_FILE = ROOT / "data" / "planner_data.json"
OUTPUT_FILE = ROOT / "dashboard.html"


def main():
    if not DATA_FILE.exists():
        raise SystemExit(f"{DATA_FILE} not found - run sync.py first.")

    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    html = planner_html.render_html(data, completed_ids=[], embedded=False)
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE} - open it in your browser.")


if __name__ == "__main__":
    main()
