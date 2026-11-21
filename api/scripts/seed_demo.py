"""Load cached benchmark outputs into a SQLite DB so the UI has data without calling Gemini.

python scripts/seed_demo.py [db_path]      # default data/demo.db; safe to re-run
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from carbontrace import store  # noqa: E402
from carbontrace.demo import seed  # noqa: E402


if __name__ == "__main__":
    db = sys.argv[1] if len(sys.argv) > 1 else "data/demo.db"
    Path(db).parent.mkdir(parents=True, exist_ok=True)
    print(f"seeded {seed(store.connect(db))} document(s) into {db}")
