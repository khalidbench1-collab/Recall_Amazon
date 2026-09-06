"""Grader tests.

These use a fake Bedrock client rather than the real one. That is not to avoid
the network: it is because the behaviour worth pinning here is what the grader
does with a response, including the responses a model should never send but
sometimes will. Calibration against the live model is a separate suite.
"""

import json

import pytest
from botocore.exceptions import ClientError

from recall.grader import NO_ANSWER, Grade, grade


class FakeBedrock:
    """Minimal stand-in for a bedrock-runtime client."""

    def __init__(self, text: str = '{"quality": 4, "explanation": "Close enough."}'):
        self.text = text
        self.calls: list[dict] = []

    def converse(self, **kwargs) -> dict:
        self.calls.append(kwargs)
        return {
            "output": {"message": {"content": [{"text": self.text}]}},
            "metrics": {"latencyMs": 900},
        }


class ExplodingBedrock:
    def __init__(self, code: str = "ThrottlingException"):
        self.code = code

    def converse(self, **kwargs) -> dict:
        raise ClientError({"Error": {"Code": self.code, "Message": "nope"}}, "Converse")


class TestGrading:
    def test_a_scored_answer_returns_the_quality(self) -> None:
        result = grade("Lima", "Lima", client=FakeBedrock())
        assert result.quality == 4

    def test_a_scored_answer_returns_the_spoken_explanation(self) -> None:
        result = grade("Lima", "Lima", client=FakeBedrock())
        assert result.explanation == "Close enough."

    def test_the_expected_answer_and_transcript_both_reach_the_model(self) -> None:
        fake = FakeBedrock()
        grade("The capital is Lima", "I think Lima", client=fake)
        sent = json.dumps(fake.calls[0])
        assert "The capital is Lima" in sent and "I think Lima" in sent


class TestNoAnswer:
    """D6: a speech recognition failure is not a memory failure."""

    @pytest.mark.parametrize("transcript", ["", "   ", "\n"])
    def test_an_empty_transcript_is_not_graded_at_all(self, transcript: str) -> None:
        assert grade("Lima", transcript, client=FakeBedrock()) == NO_ANSWER

    def test_an_empty_transcript_never_reaches_the_model(self) -> None:
        fake = FakeBedrock()
        grade("Lima", "", client=fake)
        assert fake.calls == []

    def test_no_answer_carries_no_quality(self) -> None:
        assert NO_ANSWER.quality is None


class TestDegradation:
    """A grader that guesses is worse than one that admits it failed."""

    def test_a_bedrock_failure_produces_no_quality(self) -> None:
        assert grade("Lima", "Lima", client=ExplodingBedrock()).quality is None

    def test_a_bedrock_failure_still_says_something_out_loud(self) -> None:
        result = grade("Lima", "Lima", client=ExplodingBedrock())
        assert result.explanation

    def test_unparseable_model_output_is_not_guessed_at(self) -> None:
        result = grade("Lima", "Lima", client=FakeBedrock("I'd say about a 4?"))
        assert result.quality is None

    def test_a_score_outside_the_scale_is_rejected(self) -> None:
        noisy = FakeBedrock('{"quality": 9, "explanation": "Great."}')
        assert grade("Lima", "Lima", client=noisy).quality is None

    def test_json_wrapped_in_prose_is_still_read(self) -> None:
        """Models add preambles. That is not a reason to lose the review."""
        chatty = FakeBedrock('Here you go:\n{"quality": 3, "explanation": "Partly."}')
        assert grade("Lima", "Lima", client=chatty).quality == 3


class TestGradeType:
    def test_a_grade_knows_whether_it_can_be_scheduled(self) -> None:
        assert Grade(quality=4, explanation="ok").is_scored
        assert not NO_ANSWER.is_scored
