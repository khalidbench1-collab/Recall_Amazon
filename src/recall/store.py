"""SQLite persistence: cards and an append-only review log.

Two tables, deliberately separate. `cards` holds current scheduling state;
`reviews` holds every attempt ever made. Keeping the log rather than folding it
into the card is what makes streaks possible and, more importantly, what lets
grader calibration be checked retrospectively against real answers.

See docs/ARCHITECTURE.md and decisions D6 and D7.
"""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from recall.scheduler import CardState, due_at, review

SCHEMA = """
CREATE TABLE IF NOT EXISTS cards (
    id            INTEGER PRIMARY KEY,
    prompt        TEXT    NOT NULL,
    answer        TEXT    NOT NULL,
    interval_days INTEGER NOT NULL DEFAULT 0,
    repetitions   INTEGER NOT NULL DEFAULT 0,
    ease_factor   REAL    NOT NULL DEFAULT 2.5,
    due_at        TEXT    NOT NULL,
    created_at    TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS cards_due_at ON cards (due_at);

CREATE TABLE IF NOT EXISTS reviews (
    id           INTEGER PRIMARY KEY,
    card_id      INTEGER NOT NULL REFERENCES cards (id),
    transcript   TEXT,
    quality      INTEGER,
    explanation  TEXT,
    submitted_at TEXT    NOT NULL,
    graded_at    TEXT
);

CREATE INDEX IF NOT EXISTS reviews_card_id ON reviews (card_id);
"""


@dataclass(frozen=True)
class Card:
    id: int
    prompt: str
    answer: str
    state: CardState
    due_at: datetime


@dataclass(frozen=True)
class Review:
    """One attempt at one card.

    `quality` and `graded_at` are None while grading is outstanding, which under
    D7 is the normal case rather than an error: the answer is recorded and
    acknowledged immediately, and the grade lands later or not at all.
    """

    id: int
    card_id: int
    transcript: str
    quality: int | None
    explanation: str | None
    submitted_at: datetime
    graded_at: datetime | None


def _dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


class Store:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._db = connection
        # D7 grades on a background thread, so writes arrive from more than one
        # thread. SQLite serialises them anyway; the lock is here so a read
        # never lands between the two UPDATEs that make up apply_grade().
        self._lock = threading.Lock()
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys = ON")
        self._db.executescript(SCHEMA)

    @classmethod
    @contextmanager
    def open(cls, path: Path | str) -> Iterator[Store]:
        connection = sqlite3.connect(path, check_same_thread=False)
        try:
            yield cls(connection)
        finally:
            connection.close()

    # -- cards ---------------------------------------------------------------

    def add_card(self, prompt: str, answer: str, *, created_at: datetime) -> int:
        """Add a card, due immediately. Capture is spoken, so this stays minimal."""
        cursor = self._db.execute(
            "INSERT INTO cards (prompt, answer, due_at, created_at) VALUES (?, ?, ?, ?)",
            (prompt, answer, created_at.isoformat(), created_at.isoformat()),
        )
        self._db.commit()
        return int(cursor.lastrowid)

    def get_card(self, card_id: int) -> Card:
        row = self._db.execute(
            "SELECT * FROM cards WHERE id = ?", (card_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"no card with id {card_id}")
        return self._card(row)

    def list_due_cards(self, *, now: datetime, limit: int | None = None) -> list[Card]:
        """Cards owed, oldest debt first.

        Ordering matters more than it looks: a review session is usually cut
        short, so whatever is served first is what actually gets reviewed.
        """
        sql = "SELECT * FROM cards WHERE due_at <= ? ORDER BY due_at ASC"
        params: list[object] = [now.isoformat()]
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        return [self._card(row) for row in self._db.execute(sql, params)]

    def reschedule(self, card_id: int, *, due_at: datetime) -> None:
        """Move a card's next due date without recording a review."""
        self._db.execute(
            "UPDATE cards SET due_at = ? WHERE id = ?", (due_at.isoformat(), card_id)
        )
        self._db.commit()

    # -- reviews -------------------------------------------------------------

    def submit_answer(
        self, card_id: int, transcript: str, *, submitted_at: datetime
    ) -> int:
        """Record an answer. Deliberately does not touch the schedule.

        D6 and D7 both land here: an answer that is never graded, for any
        reason, must leave the card exactly as it was. Corrupting an interval
        with a guess is worse than skipping the review entirely.
        """
        cursor = self._db.execute(
            "INSERT INTO reviews (card_id, transcript, submitted_at) VALUES (?, ?, ?)",
            (card_id, transcript, submitted_at.isoformat()),
        )
        self._db.commit()
        return int(cursor.lastrowid)

    def apply_grade(
        self, review_id: int, *, quality: int, explanation: str, graded_at: datetime
    ) -> Card:
        """Attach a grade to a submitted answer and advance the card."""
        with self._lock:
            pending = self.get_review(review_id)
            card = self.get_card(pending.card_id)

            advanced = review(card.state, quality)
            next_due = due_at(graded_at, advanced)

            self._apply(review_id, card, advanced, next_due, quality, explanation,
                        graded_at)
        return self.get_card(card.id)

    def _apply(self, review_id, card, advanced, next_due, quality, explanation,
               graded_at) -> None:
        self._db.execute(
            "UPDATE reviews SET quality = ?, explanation = ?, graded_at = ?"
            " WHERE id = ?",
            (quality, explanation, graded_at.isoformat(), review_id),
        )
        self._db.execute(
            "UPDATE cards SET interval_days = ?, repetitions = ?, ease_factor = ?,"
            " due_at = ? WHERE id = ?",
            (
                advanced.interval_days,
                advanced.repetitions,
                advanced.ease_factor,
                next_due.isoformat(),
                card.id,
            ),
        )
        self._db.commit()

    def note_ungraded(self, review_id: int, *, explanation: str) -> None:
        """Record why an answer could not be scored, without scoring it.

        The card keeps its schedule (D6) and `quality` stays null, so the review
        is still visibly ungraded in the log - but the learner hears a reason
        instead of silence, and a later audit can tell "we failed to grade this"
        apart from "we never tried".
        """
        with self._lock:
            self._db.execute(
                "UPDATE reviews SET explanation = ? WHERE id = ?",
                (explanation, review_id),
            )
            self._db.commit()

    def get_review(self, review_id: int) -> Review:
        row = self._db.execute(
            "SELECT * FROM reviews WHERE id = ?", (review_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"no review with id {review_id}")
        return self._review(row)

    def list_reviews(self, card_id: int) -> list[Review]:
        rows = self._db.execute(
            "SELECT * FROM reviews WHERE card_id = ? ORDER BY submitted_at ASC",
            (card_id,),
        )
        return [self._review(row) for row in rows]

    def streak_days(self, *, now: datetime) -> int:
        """Consecutive days up to `now` on which at least one card was graded.

        Counts graded reviews only. An answer recorded but never graded did not
        measurably happen, and inflating a streak with it would make the one
        number the user hears every day quietly dishonest.
        """
        rows = self._db.execute(
            "SELECT DISTINCT substr(graded_at, 1, 10) AS day FROM reviews"
            " WHERE graded_at IS NOT NULL"
        )
        days = {date.fromisoformat(row["day"]) for row in rows}

        streak = 0
        cursor = now.date()
        while cursor in days:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    # -- row mapping ---------------------------------------------------------

    def _card(self, row: sqlite3.Row) -> Card:
        return Card(
            id=row["id"],
            prompt=row["prompt"],
            answer=row["answer"],
            state=CardState(
                interval_days=row["interval_days"],
                repetitions=row["repetitions"],
                ease_factor=row["ease_factor"],
            ),
            due_at=_dt(row["due_at"]),
        )

    def _review(self, row: sqlite3.Row) -> Review:
        return Review(
            id=row["id"],
            card_id=row["card_id"],
            transcript=row["transcript"],
            quality=row["quality"],
            explanation=row["explanation"],
            submitted_at=_dt(row["submitted_at"]),
            graded_at=_dt(row["graded_at"]),
        )
