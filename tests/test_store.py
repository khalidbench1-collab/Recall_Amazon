"""Store tests: real SQLite against a temp file, no mocks.

The store is the only stateful component, so these are integration tests by
design. Mocking sqlite3 would test our idea of SQLite rather than SQLite.
"""

from datetime import UTC, datetime, timedelta

import pytest

from recall.store import Store

NOW = datetime(2026, 9, 6, 9, 0, tzinfo=UTC)


@pytest.fixture
def store(tmp_path):
    with Store.open(tmp_path / "test.db") as s:
        yield s


class TestCards:
    def test_an_added_card_can_be_read_back(self, store: Store) -> None:
        card_id = store.add_card("capital of Peru", "Lima", created_at=NOW)
        assert store.get_card(card_id).prompt == "capital of Peru"

    def test_a_new_card_is_due_immediately(self, store: Store) -> None:
        card_id = store.add_card("capital of Peru", "Lima", created_at=NOW)
        assert store.get_card(card_id).due_at == NOW

    def test_a_missing_card_is_reported_as_missing(self, store: Store) -> None:
        with pytest.raises(KeyError):
            store.get_card(9999)


class TestDueCards:
    def test_cards_not_yet_due_are_excluded(self, store: Store) -> None:
        card_id = store.add_card("q", "a", created_at=NOW)
        store.reschedule(card_id, due_at=NOW + timedelta(days=3))
        assert store.list_due_cards(now=NOW) == []

    def test_the_oldest_debt_comes_first(self, store: Store) -> None:
        recent = store.add_card("recent", "a", created_at=NOW)
        overdue = store.add_card("overdue", "a", created_at=NOW)
        store.reschedule(recent, due_at=NOW - timedelta(days=1))
        store.reschedule(overdue, due_at=NOW - timedelta(days=30))
        assert [c.prompt for c in store.list_due_cards(now=NOW)] == ["overdue", "recent"]

    def test_a_review_session_can_be_capped(self, store: Store) -> None:
        for i in range(5):
            store.add_card(f"q{i}", "a", created_at=NOW)
        assert len(store.list_due_cards(now=NOW, limit=3)) == 3


class TestPersistence:
    def test_cards_survive_a_restart(self, tmp_path) -> None:
        path = tmp_path / "persist.db"
        with Store.open(path) as first:
            first.add_card("capital of Peru", "Lima", created_at=NOW)
        with Store.open(path) as second:
            assert len(second.list_due_cards(now=NOW)) == 1


class TestReviewLog:
    """D7: an answer is recorded before it is graded, and grading may never
    arrive. The log has to represent that honestly."""

    def test_a_submitted_answer_is_recorded_before_it_is_graded(
        self, store: Store
    ) -> None:
        card_id = store.add_card("capital of Peru", "Lima", created_at=NOW)
        review_id = store.submit_answer(card_id, "Lima I think", submitted_at=NOW)
        assert store.get_review(review_id).quality is None

    def test_an_ungraded_answer_leaves_the_schedule_untouched(
        self, store: Store
    ) -> None:
        card_id = store.add_card("capital of Peru", "Lima", created_at=NOW)
        before = store.get_card(card_id)
        store.submit_answer(card_id, "Lima I think", submitted_at=NOW)
        assert store.get_card(card_id) == before

    def test_grading_an_answer_advances_the_card(self, store: Store) -> None:
        card_id = store.add_card("capital of Peru", "Lima", created_at=NOW)
        review_id = store.submit_answer(card_id, "Lima", submitted_at=NOW)
        store.apply_grade(review_id, quality=5, explanation="Exact.", graded_at=NOW)
        assert store.get_card(card_id).due_at == NOW + timedelta(days=1)

    def test_grading_records_the_score_and_explanation(self, store: Store) -> None:
        card_id = store.add_card("capital of Peru", "Lima", created_at=NOW)
        review_id = store.submit_answer(card_id, "Lima", submitted_at=NOW)
        store.apply_grade(review_id, quality=5, explanation="Exact.", graded_at=NOW)
        assert store.get_review(review_id).explanation == "Exact."

    def test_the_review_log_is_append_only(self, store: Store) -> None:
        """Every attempt is kept, so grader calibration can be checked later."""
        card_id = store.add_card("capital of Peru", "Lima", created_at=NOW)
        for day in range(3):
            at = NOW + timedelta(days=day)
            review_id = store.submit_answer(card_id, "Lima", submitted_at=at)
            store.apply_grade(review_id, quality=4, explanation="ok", graded_at=at)
        assert len(store.list_reviews(card_id)) == 3


class TestStreak:
    def test_days_with_no_reviews_break_the_streak(self, store: Store) -> None:
        card_id = store.add_card("q", "a", created_at=NOW)
        for day in [0, 1, 4]:
            at = NOW + timedelta(days=day)
            review_id = store.submit_answer(card_id, "a", submitted_at=at)
            store.apply_grade(review_id, quality=4, explanation="ok", graded_at=at)
        assert store.streak_days(now=NOW + timedelta(days=4)) == 1

    def test_consecutive_days_accumulate(self, store: Store) -> None:
        card_id = store.add_card("q", "a", created_at=NOW)
        for day in range(3):
            at = NOW + timedelta(days=day)
            review_id = store.submit_answer(card_id, "a", submitted_at=at)
            store.apply_grade(review_id, quality=4, explanation="ok", graded_at=at)
        assert store.streak_days(now=NOW + timedelta(days=2)) == 3
