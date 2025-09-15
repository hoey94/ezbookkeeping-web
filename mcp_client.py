import asyncio
import os
from contextlib import AsyncExitStack
from mcp import ClientSession

MCP_URL = os.getenv(
    "EZBOOKKEEPING_MCP_URL", "http://192.168.30.5:8422/mcp"
)
MCP_TOKEN = os.getenv(
    "EZBOOKKEEPING_MCP_TOKEN",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyVG9rZW5JZCI6IjE5NzkyOTc2MTI1MDA0ODIyNzkiLCJqdGkiOiIzNzc1MTQ5OTU3NjU3Mzk1MjAwIiwidXNlcm5hbWUiOiJob2V5IiwidHlwZSI6NSwiaWF0IjoxNzU3OTQxNjczLCJleHAiOjEwOTgxMzEzNzEwfQ.IzfWt5xZrKbsEOG1nCkOhUtJol3aNel8SO3G_3SDcso",
)

async def query_all_accounts(session: ClientSession) -> None:
    """Fetch and print all account names using the MCP API."""
    result = await session.call_tool("query_all_accounts", {})
    print("Accounts:")
    for account in result.data:
        print("-", account)

async def main() -> None:
    async with AsyncExitStack() as stack:
        session = ClientSession(
            MCP_URL,
            headers={"Authorization": f"Bearer {MCP_TOKEN}"},
        )
        await stack.enter_async_context(session)
        await query_all_accounts(session)

if __name__ == "__main__":
    asyncio.run(main())
