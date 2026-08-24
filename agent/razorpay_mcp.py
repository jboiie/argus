"""MCP client wiring against Razorpay's remote MCP server.

Connects with the merchant's test-mode key/secret, discovers available
tools, and calls them. Read-only calls (list_tools, fetch_*) are free to
run anytime. create_payment_link and other money-moving tools must be
mocked during bulk/automated runs (30-link test-mode cap, see PROJECT_DESC.md
Section 5) - only called for real during manual smoke tests and the demo.
"""

import base64
import os

import httpx2
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

load_dotenv()

RAZORPAY_MCP_URL = "https://mcp.razorpay.com/mcp"


def _auth_header() -> dict[str, str]:
    key_id = os.environ["RAZORPAY_KEY_ID"]
    key_secret = os.environ["RAZORPAY_KEY_SECRET"]
    token = base64.b64encode(f"{key_id}:{key_secret}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


async def list_tools() -> list[str]:
    """Read-only: returns the names of tools Razorpay's MCP server exposes."""
    http_client = httpx2.AsyncClient(headers=_auth_header())
    async with streamable_http_client(RAZORPAY_MCP_URL, http_client=http_client) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return [t.name for t in result.tools]


async def call_tool(name: str, arguments: dict) -> dict:
    http_client = httpx2.AsyncClient(headers=_auth_header())
    async with streamable_http_client(RAZORPAY_MCP_URL, http_client=http_client) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await session.call_tool(name, arguments)


async def demo():
    if not os.environ.get("RAZORPAY_KEY_ID"):
        print("RAZORPAY_KEY_ID not set - skipping live call.")
        return
    tools = await list_tools()
    assert len(tools) > 0, "expected Razorpay's MCP server to expose at least one tool"
    print(f"Connected. {len(tools)} tools available, e.g.: {tools[:5]}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(demo())
