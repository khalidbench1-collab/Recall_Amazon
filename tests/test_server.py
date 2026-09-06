"""End-to-end through a real MCP client.

Uses FastMCP's in-memory transport, which exercises the same tool registration,
schema generation and dispatch a networked client would - without a port. The
networked path is proven separately by spike/check_mcp.py.
"""

import pytest
from fastmcp import Client

from recall.grader import Grade
from recall.server import create_server
from recall.service import Service
from recall.store import Store


class Inline:
    def submit(self, fn, *args):
        fn(*args)


@pytest.fixture
def mcp(tmp_path):
    with Store.open(tmp_path / "mcp.db") as store:
        service = Service(
            store,
            grade_fn=lambda expected, transcript: Grade(5, "Exactly right."),
            executor=Inline(),
        )
        yield create_server(service)


async def call(client, name, **kwargs):
    result = await client.call_tool(name, kwargs)
    return result.content[0].text


class TestToolSurface:
    async def test_every_documented_tool_is_registered(self, mcp) -> None:
        async with Client(mcp) as client:
            names = {t.name for t in await client.list_tools()}
        assert names == {
            "add_card",
            "next_due_card",
            "submit_answer",
            "get_grade",
            "get_streak_summary",
        }

    async def test_every_tool_describes_itself_to_the_calling_model(self, mcp) -> None:
        async with Client(mcp) as client:
            tools = await client.list_tools()
        assert all(t.description and len(t.description.split()) > 15 for t in tools)


class TestFullReviewCycle:
    async def test_a_card_can_be_captured_reviewed_and_graded_over_mcp(
        self, mcp
    ) -> None:
        async with Client(mcp) as client:
            await call(client, "add_card", prompt="capital of Peru", answer="Lima")

            asked = await call(client, "next_due_card")
            assert "capital of Peru" in asked

            card_id = int(asked.rsplit("card ", 1)[1].rstrip(")"))
            submitted = await call(
                client, "submit_answer", card_id=card_id, transcript="Lima"
            )
            review_id = int(submitted.rsplit("review ", 1)[1].rstrip(")"))

            verdict = await call(client, "get_grade", review_id=review_id)
            assert "Exactly right." in verdict

    async def test_the_streak_is_reportable_over_mcp(self, mcp) -> None:
        async with Client(mcp) as client:
            assert await call(client, "get_streak_summary")


class TestHarness:
    """The browser harness is the hackathon's sanctioned simulated experience,
    so it has to actually be served - and labelled as simulated."""

    async def test_the_harness_is_served_from_the_server_root(self, mcp) -> None:
        from starlette.testclient import TestClient

        response = TestClient(mcp.http_app()).get("/")
        assert response.status_code == 200

    async def test_the_harness_declares_itself_a_simulation(self, mcp) -> None:
        from starlette.testclient import TestClient

        body = TestClient(mcp.http_app()).get("/").text
        assert "SIMULATED" in body

    async def test_the_harness_talks_to_the_real_mcp_endpoint(self, mcp) -> None:
        from starlette.testclient import TestClient

        body = TestClient(mcp.http_app()).get("/").text
        assert '"/mcp"' in body and "tools/call" in body
