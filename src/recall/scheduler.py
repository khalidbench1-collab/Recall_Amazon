"""SM-2 spaced repetition scheduling.

Pure functions only. No I/O, and the current time is passed in rather than read,
so that multi-month scheduling behaviour can be tested in milliseconds.

See docs/superpowers/specs/2026-09-04-recall-design.md, decisions D4 and D5.
"""

from dataclasses import dataclass, replace
from datetime import datetime, timedelta

MIN_EASE_FACTOR = 1.3
"""SM-2's floor. Below this a card would be reviewed so often it stops being
spaced repetition and becomes cramming."""

PASSING_QUALITY = 3
"""Scores of 3 or more count as recall. Below that the card lapses."""

PARTIAL_LAPSE_QUALITY = 2
"""A 2 means "close, but wrong" - the gist was there and the detail was not."""

PARTIAL_LAPSE_FACTOR = 0.3
"""How much of the interval a partial lapse keeps."""


@dataclass(frozen=True)
class CardState:
    """Everything SM-2 needs to know about a card between reviews."""

    interval_days: int
    repetitions: int
    ease_factor: float


NEW_CARD = CardState(interval_days=0, repetitions=0, ease_factor=2.5)
"""A card that has never been reviewed. 2.5 is SM-2's starting ease factor."""


def _next_ease_factor(ease_factor: float, quality: int) -> float:
    """SM-2's ease adjustment, clamped at the floor.

    Applied on every review, pass or fail: a card you keep fumbling should get
    easier to trigger even while its interval is being decided separately.
    """
    miss = 5 - quality
    adjusted = ease_factor + (0.1 - miss * (0.08 + miss * 0.02))
    return max(MIN_EASE_FACTOR, adjusted)


def _lapsed(state: CardState, quality: int, ease_factor: float) -> CardState:
    """Decide what a failed review costs a card.

    Classic SM-2 has one answer: back to one day, repetition history gone. It
    has to, because a self-assessing user cannot honestly distinguish "no idea"
    from "I nearly had it" once the answer is already on screen. The grader can,
    so we spend that signal here rather than discarding it.

    A 2 keeps a fraction of the interval and, crucially, keeps `repetitions`:
    one fumbled morning should not erase months of demonstrated knowledge. A 0
    or 1 means there was no recall to preserve, so the card starts over.
    """
    if quality == PARTIAL_LAPSE_QUALITY:
        return replace(
            state,
            interval_days=max(1, round(state.interval_days * PARTIAL_LAPSE_FACTOR)),
            ease_factor=ease_factor,
        )

    return replace(state, interval_days=1, repetitions=0, ease_factor=ease_factor)


def review(state: CardState, quality: int) -> CardState:
    """Advance a card's schedule given a 0-5 quality score.

    `quality` comes from the semantic grader rather than from user
    self-assessment; that substitution is the point of the project.
    """
    if not 0 <= quality <= 5:
        raise ValueError(f"quality must be between 0 and 5, got {quality}")

    ease_factor = _next_ease_factor(state.ease_factor, quality)

    if quality < PASSING_QUALITY:
        return _lapsed(state, quality, ease_factor)

    if state.repetitions == 0:
        interval_days = 1
    elif state.repetitions == 1:
        interval_days = 6
    else:
        interval_days = round(state.interval_days * ease_factor)

    return replace(
        state,
        interval_days=interval_days,
        repetitions=state.repetitions + 1,
        ease_factor=ease_factor,
    )


def due_at(reviewed_at: datetime, state: CardState) -> datetime:
    """When a card in `state` should next be shown.

    The clock is a parameter rather than a call to `now()`. That is what lets
    the tests above walk a card through ten reviews and a year of scheduling
    without waiting, and what keeps this module free of I/O (decision D5).
    """
    return reviewed_at + timedelta(days=state.interval_days)
