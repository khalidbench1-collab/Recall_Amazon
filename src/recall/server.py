"""The MCP surface: five tools over Streamable HTTP (spec 2025-11-25+).

No business logic here. This module translates between the MCP wire format and
the domain modules, and reads the clock - the one place that is allowed to,
since everything below it takes time as a parameter (D5).

Five tools rather than the four originally planned: decision D7 split grading
into `submit_answer` and `get_grade`, because Alexa+ allows a tool call about
500 ms and the fastest model available takes 557. The split is not a compromise
in speech terms - "let me think", then an answer, is how people actually talk.

Tool docstrings are written for a model to read. They are the only instructions
the calling assistant gets about when to use each tool, so they say when *not*
to use one as well as when to.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

from fastmcp import FastMCP
from starlette.responses import HTMLResponse, PlainTextResponse

from recall.config import NO_CREDENTIALS_NOTICE, bedrock_credentials_present, load_env
from recall.service import Service
from recall.store import Store


def create_server(service: Service) -> FastMCP:
    """Build the MCP app around a service. Injected so tests can drive it."""
    mcp = FastMCP("recall")

    @mcp.tool
    def add_card(prompt: str, answer: str) -> str:
        """Save something the user wants to remember, as a question and answer.

        Use when the user says they want to remember, study or be quizzed on
        something. Phrase `prompt` as a question you could ask aloud, and
        `answer` as the full correct answer in a sentence or two - it is what
        the user's spoken attempt will later be graded against, so an answer of
        one bare word grades badly.
        """
        return service.add_card(prompt, answer, now=datetime.now(UTC)).spoken

    @mcp.tool
    def next_due_card() -> str:
        """Get the single most overdue card, phrased as a question to ask aloud.

        Returns one card, never a list, because a review happens one card at a
        time. Ask the user this question, listen to their answer, then call
        `submit_answer` with what they said. Do not reveal the answer first.
        """
        reply = service.next_card(now=datetime.now(UTC))
        if reply.card_id is None:
            return reply.spoken
        return f"{reply.spoken} (card {reply.card_id})"

    @mcp.tool
    def submit_answer(card_id: int, transcript: str) -> str:
        """Record the user's spoken answer to a card. Returns immediately.

        Pass `transcript` exactly as the user said it, including hesitation and
        filler - the grader is built for speech and scores meaning, not wording,
        so cleaning it up first loses information. Grading happens in the
        background; call `get_grade` a moment later for the verdict. If you did
        not hear an answer, pass an empty string: that is recorded as no answer
        given and, deliberately, does not count as a wrong one.
        """
        reply = service.submit_answer(card_id, transcript, now=datetime.now(UTC))
        return f"{reply.spoken} (review {reply.review_id})"

    @mcp.tool
    def get_grade(review_id: int) -> str:
        """Get the verdict for an answer submitted with `submit_answer`.

        Say the result to the user as given. If it says it is still thinking,
        wait a second and call again rather than making up a score.
        """
        return service.get_grade(review_id).spoken

    @mcp.tool
    def get_streak_summary() -> str:
        """How the user is doing: current streak and how many cards are due.

        Use when the user asks how they are getting on, or to open a session.
        """
        return service.streak_summary(now=datetime.now(UTC)).spoken

    @mcp.custom_route("/", methods=["GET"])
    async def harness(request):
        """Serve the browser voice harness from the MCP server's own origin.

        Same origin means no CORS to configure and one command for a judge to
        run - and, more usefully, it means the page in the browser is talking
        to the identical endpoint Alexa+ would, rather than a demo backend
        wearing the same name.
        """
        page = Path(__file__).resolve().parents[2] / "sim" / "index.html"
        if not page.exists():
            return PlainTextResponse("sim/index.html not found", status_code=404)
        return HTMLResponse(page.read_text(encoding="utf-8"))

    return mcp


def main() -> None:  # pragma: no cover - process entry point
    load_env()

    if not bedrock_credentials_present():
        print(NO_CREDENTIALS_NOTICE, flush=True)
        print(flush=True)
    db_path = os.environ.get("RECALL_DB_PATH", "./recall.db")
    host = os.environ.get("RECALL_HOST", "0.0.0.0")
    port = int(os.environ.get("RECALL_PORT", "8080"))

    with Store.open(db_path) as store:
        create_server(Service(store)).run(transport="http", host=host, port=port)


if __name__ == "__main__":  # pragma: no cover
    main()
