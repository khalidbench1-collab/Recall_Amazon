"""SM-2 spaced repetition scheduling.

Pure functions only. No I/O, and the current time is passed in rather than read,
so that multi-month scheduling behaviour can be tested in milliseconds.

See docs/superpowers/specs/2026-09-04-recall-design.md, decisions D4 and D5.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CardState:
    """Everything SM-2 needs to know about a card between reviews."""

    interval_days: int
    repetitions: int
    ease_factor: float


def review(state: CardState, quality: int) -> CardState:
    """Advance a card's schedule given a 0-5 quality score.

    `quality` comes from the semantic grader rather than from user
    self-assessment; that substitution is the point of the project.
    """
    raise NotImplementedError("Implemented in stage 2, test-first.")
