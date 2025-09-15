import json
import os
import re
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import httpx

app = FastAPI()
templates = Jinja2Templates(directory="templates")

messages: List[dict] = []

SYSTEM_PROMPT = (
    "You are a bookkeeping assistant. When the user describes a transaction, "
    "reply only with a JSON object containing keys: date (ISO 8601), amount, "
    "account, category. Preserve any spaces in names or numbers."
)

DEEPSEEK_API_KEY = os.getenv(
    "DEEPSEEK_API_KEY",
    "sk-0b66bdc798d6405c91a27cc7848439ae",
)
DEEPSEEK_API_BASE = os.getenv(
    "DEEPSEEK_API_BASE", "https://api.deepseek.com/v1"
)
MCP_URL = os.getenv(
    "EZBOOKKEEPING_MCP_URL", "http://192.168.30.5:8422/mcp"
)
MCP_TOKEN = os.getenv(
    "EZBOOKKEEPING_MCP_TOKEN",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyVG9rZW5JZCI6IjE5NzkyOTc2MTI1MDA0ODIyNzkiLCJqdGkiOiIzNzc1MTQ5OTU3NjU3Mzk1MjAwIiwidXNlcm5hbWUiOiJob2V5IiwidHlwZSI6NSwiaWF0IjoxNzU3OTQxNjczLCJleHAiOjEwOTgxMzEzNzEwfQ.IzfWt5xZrKbsEOG1nCkOhUtJol3aNel8SO3G_3SDcso",
)


def _extract_json(text: str) -> Optional[dict]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None


async def _mcp_add_transaction(data: dict) -> str:
    if not MCP_URL or not MCP_TOKEN:
        return "MCP config missing"

    dt = datetime.fromisoformat(data["date"])
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    time_str = dt.isoformat().replace("+00:00", "Z")

    payload = {
        "name": "add_transaction",
        "arguments": {
            "type": "expense",
            "time": time_str,
            "category_name": data["category"],
            "account_name": data["account"],
            "amount": str(data["amount"]),
        },
    }

    headers = {"Authorization": f"Bearer {MCP_TOKEN}"}
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(f"{MCP_URL}/call", json=payload, headers=headers)
    response.raise_for_status()
    try:
        data = response.json()
    except ValueError:
        data = {"response": response.text}
    print("MCP response:", data)
    return json.dumps(data, ensure_ascii=False)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "messages": messages})


@app.post("/chat", response_class=HTMLResponse)
async def chat(request: Request, message: str = Form(...)):
    messages.append({"role": "user", "content": message})

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
        "mcpServers": {
            "ezbookkeeping-mcp": {
                "type": "streamable-http",
                "url": MCP_URL,
                "headers": {"Authorization": f"Bearer {MCP_TOKEN}"},
            }
        },
    }

    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
    async with httpx.AsyncClient(base_url=DEEPSEEK_API_BASE, timeout=60) as client:
        response = await client.post("/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    reply = data["choices"][0]["message"]["content"]
    transaction = _extract_json(reply)
    if transaction:
        try:
            mcp_result = await _mcp_add_transaction(transaction)
            reply += f"\n\n[MCP: {mcp_result}]"
        except Exception as exc:  # pragma: no cover - best effort
            reply += f"\n\n[MCP error: {exc}]"

    messages.append({"role": "assistant", "content": reply})
    return templates.TemplateResponse("index.html", {"request": request, "messages": messages})

