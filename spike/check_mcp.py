"""Connect to the spike server as a real MCP client over Streamable HTTP.

Not a unit test - a protocol check. It performs a genuine `initialize`
handshake, lists tools, and calls one, over HTTP rather than in-process, so a
transport-layer failure cannot hide behind a direct function call.
"""

import asyncio

from fastmcp import Client

URL = "http://127.0.0.1:8765/mcp/"


async def main() -> None:
    async with Client(URL) as client:
        tools = await client.list_tools()
        print("tools:", [t.name for t in tools])
        result = await client.call_tool("echo", {"text": "stage one"})
        print("call:", result.content[0].text)


asyncio.run(main())
