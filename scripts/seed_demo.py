"""Load the demo deck into a database so there is something to review.

    python scripts/seed_demo.py            # into ./recall.db
    python scripts/seed_demo.py my.db      # or somewhere else

Idempotent: running it twice does not duplicate the deck.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from recall.config import load_env
from recall.demo import DEMO_DECK
from recall.demo import seed as seed_deck
from recall.store import Store


def main() -> int:
    load_env()
    import os

    path = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
        "RECALL_DB_PATH", "recall.db"
    )

    with Store.open(path) as store:
        added = seed_deck(store, now=datetime.now(UTC))

    if added:
        print(f"Added {added} cards to {path}. All due now.")
    else:
        print(f"{path} already has the demo deck ({len(DEMO_DECK)} cards).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
