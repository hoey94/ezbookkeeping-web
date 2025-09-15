import os
from typing import List

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import httpx

app = FastAPI()
templates = Jinja2Templates(directory="templates")

messages: List[dict] = []

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
MCP_URL = os.getenv("EZBOOKKEEPING_MCP_URL", "")
MCP_TOKEN = os.getenv("EZBOOKKEEPING_MCP_TOKEN", "")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "messages": messages})


@app.post("/chat", response_class=HTMLResponse)
async def chat(request: Request, message: str = Form(...)):
    messages.append({"role": "user", "content": message})

    payload = {
        "model": "deepseek-chat",
        "messages": messages,
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
    messages.append({"role": "assistant", "content": reply})
    return templates.TemplateResponse("index.html", {"request": request, "messages": messages})

