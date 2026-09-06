"""Calibration: does the grader score the way a fair teacher would?

This suite calls the real model, so it is opt-in:

    RECALL_CALIBRATION=1 pytest tests/test_calibration.py -v

Everything else in the test suite runs without credentials. This one is the
evidence behind the project's central claim - that a 0-5 score produced from
outside is more trustworthy than one the learner assigns themselves after
seeing the answer - so it asserts score *bands*, not exact numbers. A grader
that lands 5 where a teacher would say 4 is fine. One that lands 5 where a
teacher would say 1 is the failure this suite exists to catch.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import pytest

from recall.grader import grade

pytestmark = pytest.mark.skipif(
    os.environ.get("RECALL_CALIBRATION") != "1",
    reason="live model calls; set RECALL_CALIBRATION=1 to run",
)


@dataclass(frozen=True)
class Case:
    name: str
    expected: str
    transcript: str
    low: int
    high: int


MITOSIS = (
    "Mitosis produces two identical diploid cells for growth and repair. "
    "Meiosis produces four genetically distinct haploid gametes."
)
EASE = (
    "How fast a card's interval grows. Each successful review multiplies the "
    "interval by the ease factor."
)

CASES = [
    Case(
        "exact answer",
        "The capital of Peru is Lima.",
        "the capital of peru is lima",
        5,
        5,
    ),
    Case(
        "correct but hedged and full of filler",
        "The capital of Peru is Lima.",
        "um I think it's uh Lima right",
        4,
        5,
    ),
    Case(
        "correct through paraphrase, no shared wording",
        EASE,
        "it decides how much longer the gap gets each time you get one right",
        4,
        5,
    ),
    Case(
        "both halves correct in the learner's own words",
        MITOSIS,
        "mitosis makes two copies that are the same for repairing you and "
        "meiosis makes four sex cells that are all different",
        4,
        5,
    ),
    Case(
        "right idea, the key distinction missing",
        MITOSIS,
        "they're both types of cell division that happen in the body",
        1,
        3,
    ),
    Case(
        "half the answer, confidently stated",
        MITOSIS,
        "mitosis makes two identical cells",
        2,
        4,
    ),
    Case(
        "right subject area, substance wrong",
        MITOSIS,
        "mitosis makes four different cells and meiosis makes two the same",
        0,
        2,
    ),
    Case(
        "confidently wrong",
        "The capital of Peru is Lima.",
        "it's definitely Rio de Janeiro",
        0,
        1,
    ),
    Case(
        "transcription mangled the word, meaning intact",
        "The capital of Peru is Lima.",
        "the capital of peru is leemah",
        4,
        5,
    ),
    Case(
        "admits not knowing",
        MITOSIS,
        "honestly I have no idea",
        0,
        1,
    ),
    Case(
        "unrelated answer",
        MITOSIS,
        "the treaty of westphalia established state sovereignty",
        0,
        1,
    ),
]


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.name)
def test_the_grader_scores_within_the_expected_band(case: Case) -> None:
    result = grade(case.expected, case.transcript)
    assert result.is_scored, f"grader returned no score: {result.explanation}"
    assert case.low <= result.quality <= case.high, (
        f"{case.name}: expected {case.low}-{case.high}, "
        f"got {result.quality} ({result.explanation})"
    )


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.name)
def test_the_spoken_explanation_stays_short_enough_to_hear(case: Case) -> None:
    result = grade(case.expected, case.transcript)
    assert len(result.explanation.split()) <= 30
