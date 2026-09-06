"""SM-2 scheduling tests.

Written first, in stage 2. The scheduler is the component where correctness
matters most and is cheapest to verify, which is why it leads the build.

The quality score is 0-5 and arrives from the semantic grader, not from user
self-assessment (decision D4). A score of 3 or more is a pass.
"""

from datetime import UTC, datetime

import pytest

from recall.scheduler import NEW_CARD, CardState, due_at, review

# A card that has been known for a long time: three months between reviews and
# an ease factor that has drifted up from repeated easy passes.
WELL_KNOWN = CardState(interval_days=90, repetitions=8, ease_factor=2.6)


class TestFirstPasses:
    """The opening intervals are fixed by the algorithm, not computed."""

    def test_a_new_card_answered_correctly_is_due_again_tomorrow(self) -> None:
        assert review(NEW_CARD, quality=4).interval_days == 1

    def test_the_second_consecutive_pass_jumps_to_six_days(self) -> None:
        first = review(NEW_CARD, quality=4)
        assert review(first, quality=4).interval_days == 6

    def test_passing_increments_the_repetition_count(self) -> None:
        assert review(NEW_CARD, quality=4).repetitions == 1


class TestEstablishedCards:
    def test_the_third_pass_onwards_multiplies_by_the_ease_factor(self) -> None:
        state = CardState(interval_days=6, repetitions=2, ease_factor=2.5)
        assert review(state, quality=4).interval_days == 15  # 6 * 2.5

    def test_intervals_are_whole_days(self) -> None:
        state = CardState(interval_days=7, repetitions=3, ease_factor=2.36)
        assert isinstance(review(state, quality=4).interval_days, int)


class TestEaseFactor:
    """Ease drifts down on hard answers and up on easy ones, and has a floor."""

    def test_a_perfect_answer_raises_the_ease_factor(self) -> None:
        assert review(NEW_CARD, quality=5).ease_factor > NEW_CARD.ease_factor

    def test_a_barely_passing_answer_lowers_the_ease_factor(self) -> None:
        assert review(NEW_CARD, quality=3).ease_factor < NEW_CARD.ease_factor

    def test_ease_factor_never_falls_below_the_floor(self) -> None:
        struggling = CardState(interval_days=1, repetitions=0, ease_factor=1.3)
        assert review(struggling, quality=0).ease_factor == pytest.approx(1.3)


class TestPurity:
    """D5: the scheduler is pure. Callers must be able to rely on that."""

    def test_review_does_not_mutate_the_state_it_is_given(self) -> None:
        before = CardState(interval_days=90, repetitions=8, ease_factor=2.6)
        review(before, quality=0)
        assert before == CardState(interval_days=90, repetitions=8, ease_factor=2.6)


class TestQualityValidation:
    @pytest.mark.parametrize("quality", [-1, 6, 100])
    def test_a_score_outside_zero_to_five_is_rejected(self, quality: int) -> None:
        with pytest.raises(ValueError):
            review(NEW_CARD, quality=quality)


class TestGradedLapse:
    """A failure is not one thing.

    Classic SM-2 throws away the difference between "no idea" and "close but
    wrong", because a self-assessing user cannot be trusted to report it. The
    grader can, so the scheduler uses it.
    """

    def test_a_blank_answer_resets_a_well_known_card_to_one_day(self) -> None:
        assert review(WELL_KNOWN, quality=0).interval_days == 1

    def test_a_barely_wrong_answer_also_resets_when_there_was_no_recall(self) -> None:
        assert review(WELL_KNOWN, quality=1).interval_days == 1

    def test_a_close_but_wrong_answer_keeps_thirty_percent_of_the_interval(self) -> None:
        assert review(WELL_KNOWN, quality=2).interval_days == 27  # round(90 * 0.3)

    def test_a_close_but_wrong_answer_preserves_the_repetition_history(self) -> None:
        assert review(WELL_KNOWN, quality=2).repetitions == WELL_KNOWN.repetitions

    def test_total_failure_discards_the_repetition_history(self) -> None:
        assert review(WELL_KNOWN, quality=0).repetitions == 0

    def test_a_partial_lapse_never_rounds_down_to_zero_days(self) -> None:
        short = CardState(interval_days=2, repetitions=4, ease_factor=2.5)
        assert review(short, quality=2).interval_days == 1

    def test_a_partial_lapse_still_costs_ease(self) -> None:
        assert review(WELL_KNOWN, quality=2).ease_factor < WELL_KNOWN.ease_factor


class TestDueDates:
    """D5: the clock is injected. Nothing here reads the wall clock."""

    def test_the_next_review_is_the_interval_away_from_this_one(self) -> None:
        reviewed_at = datetime(2026, 9, 6, 8, 30, tzinfo=UTC)
        state = CardState(interval_days=6, repetitions=2, ease_factor=2.5)
        assert due_at(reviewed_at, state) == datetime(
            2026, 9, 12, 8, 30, tzinfo=UTC
        )

    def test_a_brand_new_card_is_due_immediately(self) -> None:
        reviewed_at = datetime(2026, 9, 6, tzinfo=UTC)
        assert due_at(reviewed_at, NEW_CARD) == reviewed_at

    def test_intervals_cross_a_year_within_ten_perfect_reviews(self) -> None:
        """The point of spaced repetition: effort per card collapses over time."""
        state = NEW_CARD
        for _ in range(10):
            state = review(state, quality=5)
        assert state.interval_days > 365

    def test_a_struggling_card_stays_frequent_over_many_reviews(self) -> None:
        """The mirror case: a card you keep failing must not drift away."""
        state = NEW_CARD
        for quality in [5, 5, 5, 0, 5, 5, 0, 5, 0, 1]:
            state = review(state, quality)
        assert state.interval_days <= 7
