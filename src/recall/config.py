"""Configuration loading.

One job: make a gitignored `.env` behave like the environment, so credentials
live in exactly one place and never in shell history or a commit.

Hand-rolled rather than depending on python-dotenv. The whole of it is below,
it has no behaviour worth a dependency, and one fewer install step matters when
a judge is trying to run this in under five minutes.
"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_ENV_FILE = Path(".env")


def load_env(path: Path | str = DEFAULT_ENV_FILE) -> None:
    """Read KEY=VALUE lines from `path` into os.environ.

    Real environment variables win: `setdefault` means a value already set by
    the shell, a container, or a task definition is never clobbered by a stray
    local file.
    """
    path = Path(path)
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip().strip("\"'")
        if value:
            os.environ.setdefault(key.strip(), value)
