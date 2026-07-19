"""MCP 라우터 — 앱이 MCP 클라이언트로서 우리 MCP 서버를 사용하는 시연.

- POST /api/mcp/tools : 서버가 노출한 도구 목록
- POST /api/mcp/call  : 도구 1건 호출

학습용 시연이라 매 요청마다 서버 subprocess를 stdio로 기동한다(운영 구조 아님).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.mcp import client as mcp_client

router = APIRouter(prefix="/api/mcp", tags=["mcp"])


class CallRequest(BaseModel):
    name: str = Field(min_length=1, description="호출할 MCP 도구 이름")
    arguments: dict[str, Any] = Field(default_factory=dict)


@router.post("/tools")
async def list_mcp_tools() -> dict:
    """MCP 서버가 노출한 도구 목록을 반환한다."""
    tools = await mcp_client.list_tools()
    return {"count": len(tools), "tools": tools}


@router.post("/call")
async def call_mcp_tool(body: CallRequest) -> dict:
    """MCP 도구를 호출하고 결과를 반환한다."""
    return await mcp_client.call_tool(body.name, body.arguments)
