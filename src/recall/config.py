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


def bedrock_credentials_present() -> bool:
    """Whether anything in the environment could authenticate a Bedrock call.

    Deliberately a guess rather than a live check: a network call at startup
    would slow every launch to prove something the first grading attempt proves
    anyway. This exists so the server can say *why* grading will fail, instead
    of leaving someone to discover it one review at a time.
    """
    if os.environ.get("AWS_BEARER_TOKEN_BEDROCK"):
        return True
    if os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY"):
        return True
    if os.environ.get("AWS_PROFILE"):
        return True
    return (Path.home() / ".aws" / "credentials").exists()


NO_CREDENTIALS_NOTICE = """  Recall is running WITHOUT Bedrock credentials.

  Everything works except grading: cards can be added, asked, answered and
  listed, and answers are recorded. Answers will come back ungraded, and - by
  design - an ungraded answer never changes a card's schedule, so nothing is
  corrupted by running this way.

  To enable grading: copy .env.example to .env and set AWS_BEARER_TOKEN_BEDROCK
  to a Bedrock API key (Bedrock console -> Discover -> API keys)."""
