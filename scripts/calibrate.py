"""Run the calibration cases and print the results as a Markdown table.

The test suite asserts the grader stays inside its bands. This prints what it
actually said, which is the more persuasive artefact: a reader can judge for
themselves whether the scores are fair, rather than trusting that a green test
means what we claim it means.

    python scripts/calibrate.py > docs/CALIBRATION.md
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))

from recall.config import load_env

load_env()

import os

from test_calibration import CASES

from recall.grader import DEFAULT_MODEL_ID, grade


def main() -> int:
    # Windows consoles default to cp1252; the model writes em dashes.
    sys.stdout.reconfigure(encoding="utf-8")
    model = os.environ.get("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID)
    stamp = datetime.now(UTC).strftime("%d %B %Y")

    print("# Grader calibration")
    print()
    print(
        "Every case below was scored by the live model. The bands are what a "
        "fair teacher would accept; the scores are what the grader actually "
        "produced. Reproduce with `RECALL_CALIBRATION=1 pytest "
        "tests/test_calibration.py`."
    )
    print()
    print(f"**Model:** `{model}`  ")
    print(f"**Run:** {stamp}")
    print()
    print("| Case | What the learner said | Band | Score | What it said back |")
    print("|---|---|---|---|---|")

    failures = 0
    for case in CASES:
        result = grade(case.expected, case.transcript)
        score = result.quality if result.is_scored else "-"
        inside = result.is_scored and case.low <= result.quality <= case.high
        if not inside:
            failures += 1
        mark = "" if inside else " **!**"
        said = case.transcript.replace("|", "/")
        note = result.explanation.replace("|", "/")
        print(
            f"| {case.name} | {said} | {case.low}-{case.high} "
            f"| {score}{mark} | {note} |"
        )

    print()
    print(f"**{len(CASES) - failures} of {len(CASES)} inside band.**")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
