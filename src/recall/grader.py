"""Semantic grading of a spoken answer, via Amazon Bedrock.

Runs server-side by design (decision D3): keeping the scoring prompt and its
calibration inside this repo is what makes the grading ours rather than the
calling platform's, and is what qualifies the AWS Builder mini challenge.

The output is a 0-5 quality score, which is exactly the input SM-2 has always
wanted and never honestly had. Everything here exists to make that number
trustworthy, and to refuse to produce one when it would not be.
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)

DEFAULT_MODEL_ID = "us.anthropic.claude-sonnet-4-6"
DEFAULT_REGION = "us-east-1"

SYSTEM_PROMPT = """\
You grade spoken answers to flashcards. The answer was transcribed from speech,
so it will be informal, unpunctuated, and may contain transcription errors.

Grade what the person MEANT, not the words they used. Synonyms, paraphrases,
hedging ("I think", "something like") and filler are not mistakes. A missing
detail is a mistake. A confident statement of something false is a worse
mistake than admitting uncertainty.

Use this scale:
5 - complete and correct, including the key detail
4 - correct, minor omission or imprecision
3 - the main idea is right but something important is missing
2 - partially right, or the right area with the substance wrong
1 - mostly wrong, but some relevant recall
0 - wrong, or no relevant recall at all

Reply with JSON only, no other text:
{"quality": <0-5>, "explanation": "<one short sentence, spoken aloud to the learner>"}

The explanation is read out loud. Keep it under twenty words, address the
learner as "you", and say what was missing rather than repeating the whole
answer."""

USER_TEMPLATE = """\
Expected answer:
{expected}

What the learner said:
{transcript}"""


@dataclass(frozen=True)
class Grade:
    """A grading outcome, which may legitimately carry no score.

    `quality` is None whenever we could not honestly produce a number: no
    answer was given, Bedrock failed, or the model returned something we will
    not guess at. Callers must leave the schedule alone in that case (D6, D7).
    """

    quality: int | None
    explanation: str

    @property
    def is_scored(self) -> bool:
        return self.quality is not None


NO_ANSWER = Grade(
    quality=None,
    explanation="I didn't catch an answer, so I'll leave this card where it is.",
)

GRADING_UNAVAILABLE = Grade(
    quality=None,
    explanation="I couldn't grade that one just now, so this card is unchanged.",
)


def _extract_json(text: str) -> dict | None:
    """Pull the JSON object out of a model reply.

    Models add preambles. Losing a review to a stray "Here you go:" would be a
    silly way to corrupt someone's schedule, so we look for the object rather
    than insisting the whole reply is one.
    """
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _client():
    return boto3.client(
        "bedrock-runtime", region_name=os.environ.get("AWS_REGION", DEFAULT_REGION)
    )


def grade(expected: str, transcript: str, *, client=None, model_id: str | None = None):
    """Score a spoken answer against the expected one.

    Never raises. Every failure path returns an unscored Grade, because the
    caller's only safe response to "something went wrong" is to leave the card
    untouched, and that is easier to get right if there is one return type.
    """
    if not transcript or not transcript.strip():
        return NO_ANSWER

    client = client or _client()
    model_id = model_id or os.environ.get("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID)

    try:
        response = client.converse(
            modelId=model_id,
            system=[{"text": SYSTEM_PROMPT}],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "text": USER_TEMPLATE.format(
                                expected=expected, transcript=transcript
                            )
                        }
                    ],
                }
            ],
            inferenceConfig={"maxTokens": 200, "temperature": 0},
        )
        text = response["output"]["message"]["content"][0]["text"]
    except (ClientError, BotoCoreError, KeyError, IndexError) as error:
        # Never raised to the caller - a failed grade must not break a review -
        # but silence here is how you lose an afternoon to a missing credential.
        logger.warning("grading call failed (%s): %s", model_id, error)
        return GRADING_UNAVAILABLE

    parsed = _extract_json(text)
    if parsed is None:
        logger.warning("grader returned unparseable output: %r", text[:200])
        return GRADING_UNAVAILABLE

    quality = parsed.get("quality")
    if not isinstance(quality, int) or not 0 <= quality <= 5:
        return GRADING_UNAVAILABLE

    explanation = str(parsed.get("explanation") or "").strip()
    return Grade(quality=quality, explanation=explanation or "Graded.")
