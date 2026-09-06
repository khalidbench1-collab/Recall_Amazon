"""Stage 1 spike: the smallest possible MCP server over Streamable HTTP.

This exists to prove the transport works end to end before any Recall domain
code is written. It is deliberately not `recall.server` - nothing here is meant
to survive stage 5. Run it, point a client at http://127.0.0.1:8765/mcp/, and
delete your doubts.
"""

from fastmcp import FastMCP

mcp = FastMCP("recall-spike")


@mcp.tool
def echo(text: str) -> str:
    """Return the text you were given, so a client can prove the round trip."""
    return f"recall-spike heard: {text}"


if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8765)
