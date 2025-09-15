"""Simple fastmcp client for ezBookkeeping.

This module provides an asynchronous client wrapper around the
Model Context Protocol (MCP) API exposed by ezBookkeeping.
The MCP server URL and token can be configured through the
``EZBOOKKEEPING_MCP_URL`` and ``EZBOOKKEEPING_MCP_TOKEN``
environment variables.
"""
from __future__ import annotations

import asyncio
import os
from typing import Any, Dict

from fastmcp import Client


MCP_URL = os.getenv(
    "EZBOOKKEEPING_MCP_URL", "http://192.168.30.5:8422/mcp"
)
MCP_TOKEN = os.getenv(
    "EZBOOKKEEPING_MCP_TOKEN",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyVG9rZW5JZCI6IjE5NzkyOTc2MTI1MDA0ODIyNzkiLCJqdGkiOiIzNzc1MTQ5OTU3NjU3Mzk1MjAwIiwidXNlcm5hbWUiOiJob2V5IiwidHlwZSI6NSwiaWF0IjoxNzU3OTQxNjczLCJleHAiOjEwOTgxMzEzNzEwfQ.IzfWt5xZrKbsEOG1nCkOhUtJol3aNel8SO3G_3SDcso",
)


class EzBookkeepingMCPClient:
    """Asynchronous wrapper for calling ezBookkeeping MCP tools."""

    def __init__(self, url: str = MCP_URL, token: str = MCP_TOKEN) -> None:
        self._client = Client(server=url, headers={"Authorization": f"Bearer {token}"})

    async def _call(self, tool: str, params: Dict[str, Any]) -> Any:
        async with self._client as client:
            return await client.call(tool, params)

    async def add_transaction(self, **transaction: Any) -> Any:
        """Add a transaction to ezBookkeeping."""
        return await self._call("add_transaction", transaction)

    async def query_transactions(self, **filters: Any) -> Any:
        """Query transactions using optional filters."""
        return await self._call("query_transactions", filters)

    async def query_all_accounts(self) -> Any:
        return await self._call("query_all_accounts", {})

    async def query_all_transaction_categories(self) -> Any:
        return await self._call("query_all_transaction_categories", {})

    async def query_all_transaction_tags(self) -> Any:
        return await self._call("query_all_transaction_tags", {})

    async def query_latest_exchange_rates(self, currencies: str) -> Any:
        return await self._call("query_latest_exchange_rates", {"currencies": currencies})


async def _demo() -> None:
    client = EzBookkeepingMCPClient()
    accounts = await client.query_all_accounts()
    print("Accounts:", accounts)


if __name__ == "__main__":
    asyncio.run(_demo())
