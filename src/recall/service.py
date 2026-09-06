"""Conversation logic: the layer between MCP tools and the domain.

Everything here returns a `Reply`, whose `spoken` field is written to be heard
rather than read. That constraint is not cosmetic. A response that scans fine as
JSON becomes unbearable at speaking speed, and an assistant that reads out a
bulleted list of nine due cards has failed at the only interface it has.

The other thing this layer owns is decision D7: `submit_answer` records an
answer and returns immediately, then grades in the background, because Alexa+
allows a tool roughly 500 ms and the fastest model we measured takes 557.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime

from recall.grader import grade as default_grade
from recall.store import Store

logger = logging.getLogger(__name__)

MAX_SPOKEN_WORDS = 60
"""Roughly twenty seconds of speech. Past that a listener stops listening."""

MAX_LISTED_CARDS = 3
"""Enumerations longer than this are unfollowable out loud."""


@dataclass(frozen=True)
class Reply:
    """Something to say, plus the ids a client may need to continue."""

    spoken: str
    card_id: int | None = None
    review_id: int | None = None
    quality: int | None = None


def _shape(text: str) -> str:
    """Strip markup and cap length, so anything we emit is speakable."""
    for ch in "*_#`<>":
        text = text.replace(ch, "")
    words = text.split()
    if len(words) > MAX_SPOKEN_WORDS:
        text = " ".join(words[:MAX_SPOKEN_WORDS]).rstrip(",.;:") + "."
    return " ".join(text.split())


class Service:
    def __init__(self, store: Store, *, grade_fn=None, executor=None) -> None:
        self._store = store
        self._grade = grade_fn or default_grade
        # `None` means grade nothing in the background - used by tests that want
        # to observe the pending state D7 creates.
        self._executor = (
            executor if executor is not None else ThreadPoolExecutor(max_workers=2)
        )

    # -- capture -------------------------------------------------------------

    def add_card(self, prompt: str, answer: str, *, now: datetime) -> Reply:
        card_id = self._store.add_card(prompt, answer, created_at=now)
        return Reply(
            spoken=_shape(f"Saved. I'll ask you about {prompt} next time."),
            card_id=card_id,
        )

    # -- review --------------------------------------------------------------

    def next_card(self, *, now: datetime) -> Reply:
        """The single most overdue card, spoken as a question.

        One card, not a list. The answer to "what do I owe?" is a thing to do,
        not an inventory, and reading out nine prompts is how a review session
        ends before it starts.
        """
        due = self._store.list_due_cards(now=now, limit=1)
        if not due:
            return Reply(spoken="Nothing is due right now. Enjoy the break.")

        card = due[0]
        return Reply(spoken=_shape(card.prompt), card_id=card.id)

    def submit_answer(self, card_id: int, transcript: str, *, now: datetime) -> Reply:
        """Record an answer and return at once. Grading happens after (D7)."""
        review_id = self._store.submit_answer(card_id, transcript, submitted_at=now)

        if self._executor is not None:
            self._executor.submit(self._grade_in_background, review_id, now)

        return Reply(spoken="Got it, let me think.", review_id=review_id)

    def _grade_in_background(self, review_id: int, now: datetime) -> None:
        try:
            pending = self._store.get_review(review_id)
            card = self._store.get_card(pending.card_id)
            result = self._grade(card.answer, pending.transcript)
            if result.is_scored:
                self._store.apply_grade(
                    review_id,
                    quality=result.quality,
                    explanation=result.explanation,
                    graded_at=now,
                )
            else:
                # D6: leave the schedule alone, but keep what was said so the
                # learner hears an explanation rather than silence.
                self._store.note_ungraded(review_id, explanation=result.explanation)
        except Exception:  # pragma: no cover - background work must not die quietly
            logger.exception("background grading failed for review %s", review_id)

    def get_grade(self, review_id: int) -> Reply:
        review = self._store.get_review(review_id)

        if review.quality is None and review.explanation is None:
            return Reply(spoken="I'm still thinking about that one.", review_id=review_id)

        if review.quality is None:
            return Reply(spoken=_shape(review.explanation), review_id=review_id)

        card = self._store.get_card(review.card_id)
        when = self._when(card.state.interval_days)
        return Reply(
            spoken=_shape(f"{review.explanation} I'll ask you again {when}."),
            review_id=review_id,
            card_id=card.id,
            quality=review.quality,
        )

    @staticmethod
    def _when(days: int) -> str:
        if days <= 1:
            return "tomorrow"
        if days < 14:
            return f"in {days} days"
        if days < 60:
            return f"in about {round(days / 7)} weeks"
        return f"in about {round(days / 30)} months"

    # -- summary -------------------------------------------------------------

    def streak_summary(self, *, now: datetime) -> Reply:
        streak = self._store.streak_days(now=now)
        due = len(self._store.list_due_cards(now=now))

        if streak == 0 and due == 0:
            return Reply(spoken="Nothing due, and no reviews yet today.")

        parts = []
        if streak:
            day_word = "day" if streak == 1 else "days"
            parts.append(f"You're on a {streak} {day_word} streak")
        if due:
            card_word = "card" if due == 1 else "cards"
            parts.append(f"{due} {card_word} due")
        else:
            parts.append("nothing due right now")

        return Reply(spoken=_shape(", and ".join(parts) + "."))
