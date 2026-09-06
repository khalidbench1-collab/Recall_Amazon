"""Service tests: the conversation logic, without MCP in the way.

Everything asserted here is about what the learner *hears*, because that is the
product. The MCP layer above this is plumbing and is tested separately.
"""

from datetime import UTC, datetime, timedelta

import pytest

from recall.grader import GRADING_UNAVAILABLE, Grade
from recall.service import MAX_SPOKEN_WORDS, Service
from recall.store import Store

NOW = datetime(2026, 9, 7, 9, 0, tzinfo=UTC)


class Inline:
    """Runs background work immediately, so tests stay deterministic."""

    def submit(self, fn, *args):
        fn(*args)


@pytest.fixture
def store(tmp_path):
    with Store.open(tmp_path / "svc.db") as s:
        yield s


def make_service(store: Store, grade_fn=None) -> Service:
    return Service(
        store,
        grade_fn=grade_fn or (lambda expected, transcript: Grade(4, "Close enough.")),
        executor=Inline(),
    )


class TestCapture:
    def test_a_card_can_be_added_by_voice(self, store: Store) -> None:
        service = make_service(store)
        service.add_card("capital of Peru", "Lima", now=NOW)
        assert len(store.list_due_cards(now=NOW)) == 1

    def test_adding_a_card_confirms_out_loud(self, store: Store) -> None:
        service = make_service(store)
        assert service.add_card("capital of Peru", "Lima", now=NOW).spoken


class TestReviewFlow:
    def test_nothing_due_is_said_plainly(self, store: Store) -> None:
        service = make_service(store)
        assert "nothing" in service.next_card(now=NOW).spoken.lower()

    def test_the_next_card_speaks_its_prompt(self, store: Store) -> None:
        service = make_service(store)
        service.add_card("capital of Peru", "Lima", now=NOW)
        assert "capital of Peru" in service.next_card(now=NOW).spoken

    def test_the_next_card_never_speaks_the_answer(self, store: Store) -> None:
        """Saying the answer with the question would defeat the entire exercise."""
        service = make_service(store)
        service.add_card("capital of Peru", "Lima", now=NOW)
        assert "Lima" not in service.next_card(now=NOW).spoken

    def test_submitting_an_answer_returns_before_grading_finishes(
        self, store: Store
    ) -> None:
        """D7: the reply must not wait on a model call."""
        service = make_service(store)
        card_id = service.add_card("capital of Peru", "Lima", now=NOW).card_id
        result = service.submit_answer(card_id, "Lima", now=NOW)
        assert result.review_id is not None

    def test_a_graded_answer_reports_the_verdict(self, store: Store) -> None:
        service = make_service(store)
        card_id = service.add_card("capital of Peru", "Lima", now=NOW).card_id
        review_id = service.submit_answer(card_id, "Lima", now=NOW).review_id
        assert "Close enough." in service.get_grade(review_id).spoken

    def test_a_graded_answer_advances_the_card(self, store: Store) -> None:
        service = make_service(store)
        card_id = service.add_card("capital of Peru", "Lima", now=NOW).card_id
        service.submit_answer(card_id, "Lima", now=NOW)
        assert store.get_card(card_id).due_at > NOW


class TestUngradedAnswers:
    """D6 and D7: an answer we could not score must cost the learner nothing."""

    def test_a_failed_grade_leaves_the_card_exactly_as_it_was(
        self, store: Store
    ) -> None:
        service = make_service(store, grade_fn=lambda e, t: GRADING_UNAVAILABLE)
        card_id = service.add_card("capital of Peru", "Lima", now=NOW).card_id
        before = store.get_card(card_id)
        service.submit_answer(card_id, "Lima", now=NOW)
        assert store.get_card(card_id) == before

    def test_a_failed_grade_says_so_rather_than_going_quiet(
        self, store: Store
    ) -> None:
        service = make_service(store, grade_fn=lambda e, t: GRADING_UNAVAILABLE)
        card_id = service.add_card("capital of Peru", "Lima", now=NOW).card_id
        review_id = service.submit_answer(card_id, "Lima", now=NOW).review_id
        assert service.get_grade(review_id).spoken

    def test_a_grade_still_pending_says_so(self, store: Store) -> None:
        service = Service(store, grade_fn=lambda e, t: Grade(4, "ok"), executor=None)
        card_id = service.add_card("q", "a", now=NOW).card_id
        review_id = store.submit_answer(card_id, "a", submitted_at=NOW)
        assert "still" in service.get_grade(review_id).spoken.lower()


class TestSpeechShaping:
    """A response that reads fine can be unbearable heard."""

    def test_every_spoken_response_is_short_enough_to_hear(
        self, store: Store
    ) -> None:
        service = make_service(store)
        service.add_card("capital of Peru", "Lima", now=NOW)
        for reply in [
            service.next_card(now=NOW),
            service.streak_summary(now=NOW),
            service.add_card("q", "a", now=NOW),
        ]:
            assert len(reply.spoken.split()) <= MAX_SPOKEN_WORDS

    def test_spoken_responses_contain_no_markup(self, store: Store) -> None:
        service = make_service(store)
        service.add_card("capital of Peru", "Lima", now=NOW)
        spoken = service.next_card(now=NOW).spoken
        assert not any(ch in spoken for ch in "*_#`<>")


class TestStreak:
    def test_an_empty_history_is_reported_without_a_number(
        self, store: Store
    ) -> None:
        service = make_service(store)
        assert service.streak_summary(now=NOW).spoken

    def test_a_streak_is_reported_after_reviewing(self, store: Store) -> None:
        service = make_service(store)
        card_id = service.add_card("q", "a", now=NOW).card_id
        service.submit_answer(card_id, "a", now=NOW)
        assert "1" in service.streak_summary(now=NOW).spoken

    def test_due_count_reflects_the_backlog(self, store: Store) -> None:
        service = make_service(store)
        for i in range(3):
            service.add_card(f"q{i}", "a", now=NOW - timedelta(days=1))
        assert "3" in service.streak_summary(now=NOW).spoken
