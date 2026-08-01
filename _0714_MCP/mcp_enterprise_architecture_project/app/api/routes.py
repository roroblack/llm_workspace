"""
FastAPI REST API 엔드포인트를 정의합니다.
"""

# FastAPI Router와 HTTPException을 가져옵니다.
from fastapi import APIRouter, HTTPException

# 요청 모델을 가져옵니다.
from app.api.schemas import AssistantRequest, ToolCallRequest

# 설정을 가져옵니다.
from app.core.settings import get_settings

# Assistant 서비스를 가져옵니다.
from app.services.assistant_service import AssistantService

# MCP Client 서비스를 가져옵니다.
from mcp_client.client import MCPClientService


# /api 접두어를 사용하는 Router를 생성합니다.
router = APIRouter(prefix="/api", tags=["MCP Enterprise Architecture"])

# Assistant 서비스를 생성합니다.
assistant_service = AssistantService()

# MCP Client 서비스를 생성합니다.
mcp_client = MCPClientService()


# 상태 확인 API를 정의합니다.
@router.get("/health")
def health() -> dict:
    """현재 서버와 외부 연결 모드를 반환합니다."""

    # 설정을 가져옵니다.
    settings = get_settings()

    # 민감정보를 제외한 상태를 반환합니다.
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "live_mode": settings.live_mode,
        "openai_configured": bool(settings.openai_api_key),
        "openai_model": settings.openai_model,
    }


# MCP Tool 목록 API를 정의합니다.
@router.get("/mcp/tools")
async def list_mcp_tools() -> dict:
    """MCP 서버가 제공하는 전체 Tool 목록을 반환합니다."""

    # MCP 호출 오류를 HTTP 오류로 변환합니다.
    try:
        # Tool 목록을 조회합니다.
        tools = await mcp_client.list_tools()

        # 개수와 목록을 반환합니다.
        return {"count": len(tools), "tools": tools}
    except Exception as exc:
        # 내부 오류를 HTTP 500으로 변환합니다.
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# MCP Tool 직접 호출 API를 정의합니다.
@router.post("/mcp/call")
async def call_mcp_tool(request: ToolCallRequest) -> dict:
    """MCP Client를 통해 MCP Server의 Tool을 직접 호출합니다."""

    # Tool 오류를 HTTP 응답으로 변환합니다.
    try:
        # 지정한 Tool을 호출합니다.
        return await mcp_client.call_tool(request.name, request.arguments)
    except Exception as exc:
        # 잘못된 Tool 또는 외부 시스템 오류를 HTTP 500으로 반환합니다.
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# OpenAI + MCP Assistant API를 정의합니다.
@router.post("/assistant")
async def assistant(request: AssistantRequest) -> dict:
    """자연어 요청을 분석하여 필요한 MCP Tool을 호출합니다."""

    # Assistant 처리 오류를 HTTP 응답으로 변환합니다.
    try:
        # 사용자 요청을 처리하여 반환합니다.
        return await assistant_service.ask(request.message)
    except Exception as exc:
        # 오류를 HTTP 500으로 반환합니다.
        raise HTTPException(status_code=500, detail=str(exc)) from exc
