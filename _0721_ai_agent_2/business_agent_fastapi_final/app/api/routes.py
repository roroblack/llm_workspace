# -*- coding: utf-8 -*-
"""Business Agent FastAPI의 REST API 라우터입니다."""

# 보고서 파일을 다운로드하기 위해 FileResponse를 가져옵니다.
from fastapi.responses import FileResponse
# API 경로와 오류 응답을 정의하기 위해 FastAPI 클래스를 가져옵니다.
from fastapi import APIRouter, HTTPException
# 환경변수와 파일 경로 확인을 위해 os와 Path를 가져옵니다.
import os
from pathlib import Path
# 요청 스키마를 가져옵니다.
from app.models.schemas import A2AMessageRequest, ChatRequest, PromptLabRequest, ToolCallRequest
# LangGraph 워크플로우를 가져옵니다.
from app.graph.workflow import workflow
# Prompt Engineering 실습용 직접 호출 서비스를 가져옵니다.
from app.services.prompt_lab_service import run_prompt_lab
# A2A 카드와 호출 함수를 가져옵니다.
from app.a2a.specialists import AGENT_CARDS, invoke_specialist
# MCP 공유 도구를 가져옵니다.
from app.mcp_server.tools import mcp_csv_preview, mcp_data_summary, mcp_file_list, mcp_monthly_sales
# 데이터와 RAG 서비스를 가져옵니다.
from app.services.data_service import list_data_files
from app.services.rag_service import reset_rag
# 보고서 폴더 경로를 가져옵니다.
from app.core.settings import REPORTS_DIR

# 모든 REST API에 /api/v1 접두어를 적용하는 라우터를 생성합니다.
router = APIRouter(prefix="/api/v1")


@router.get("/health")
def health() -> dict[str, object]:
    """서버와 API 키 설정 상태를 반환합니다."""
    # 비밀값 자체는 노출하지 않고 존재 여부만 반환합니다.
    return {"status": "ok", "openai_key": bool(os.getenv("OPENAI_API_KEY")), "gemini_key": bool(os.getenv("GOOGLE_API_KEY")), "architecture": ["ReAct", "RAG", "A2A", "LangGraph", "MCP"]}


@router.post("/chat")
def chat(request: ChatRequest) -> dict[str, object]:
    """LangGraph가 적절한 실행 경로를 선택해 최종 답변을 생성합니다."""
    try:
        # 요청 정보를 초기 상태로 전달해 그래프를 실행합니다.
        result = workflow.invoke({"message": request.message, "provider": request.provider, "thread_id": request.thread_id, "trace": []})
        # 프론트엔드가 필요한 핵심 필드를 구조화해 반환합니다.
        return {"answer": result.get("answer", ""), "route": result.get("route"), "target_agent": result.get("target_agent"), "sources": result.get("sources", []), "trace": result.get("trace", [])}
    except Exception as error:
        # 내부 예외를 500 오류와 사람이 읽을 수 있는 메시지로 변환합니다.
        raise HTTPException(status_code=500, detail=f"{type(error).__name__}: {error}") from error


@router.post("/prompt-lab")
def prompt_lab(request: PromptLabRequest) -> dict[str, object]:
    """Prompt Engineering 실습: 지정한 프롬프트·파라미터로 LLM 을 직접 호출합니다."""
    try:
        # LangGraph 분류를 건너뛰고 사용자가 지정한 프롬프트 설정을 그대로 실행합니다.
        return run_prompt_lab(
            message=request.message,
            provider=request.provider,
            prompt_type=request.prompt_type,
            system_prompt=request.system_prompt,
            instruction=request.instruction,
            temperature=request.temperature,
            top_p=request.top_p,
            few_shot=request.few_shot,
        )
    except SystemExit as error:
        # require_key 는 API 키가 없을 때 SystemExit 을 던지므로 안내 메시지로 변환합니다.
        raise HTTPException(status_code=400, detail=f".env 에 API 키를 설정하세요: {error}") from error
    except Exception as error:
        # 그 밖의 실행 오류를 사람이 읽을 수 있는 500 오류로 변환합니다.
        raise HTTPException(status_code=500, detail=f"{type(error).__name__}: {error}") from error


@router.post("/tools/call")
def call_tool(request: ToolCallRequest) -> dict[str, object]:
    """독립 MCP 서버와 동일한 도구를 HTTP에서 직접 실행합니다."""
    try:
        # 요청한 도구명에 따라 공유 함수를 선택합니다.
        if request.tool_name == "monthly_sales":
            result = mcp_monthly_sales(request.month)
        elif request.tool_name == "csv_preview":
            result = mcp_csv_preview(request.filename, request.limit)
        elif request.tool_name == "data_summary":
            result = mcp_data_summary()
        else:
            result = mcp_file_list()
        # 도구명과 실행 결과를 반환합니다.
        return {"tool": request.tool_name, "result": result}
    except Exception as error:
        # 잘못된 파일명이나 월 입력을 400 오류로 반환합니다.
        raise HTTPException(status_code=400, detail=f"{type(error).__name__}: {error}") from error


@router.get("/a2a/agents")
def a2a_agents() -> list[dict[str, object]]:
    """현재 서비스가 제공하는 전문 에이전트 카드를 반환합니다."""
    # 미리 정의한 에이전트 카드 목록을 반환합니다.
    return AGENT_CARDS


@router.get("/.well-known/agent-card.json")
def agent_card() -> dict[str, object]:
    """통합 Business Agent의 A2A Agent Card를 반환합니다."""
    # 서비스 이름과 전문 기능 목록을 표준 카드 형태로 반환합니다.
    return {"name": "business-agent-orchestrator", "description": "매출, 보고서, 정책 RAG와 전략 분석을 조정하는 비즈니스 에이전트", "version": "1.0.0", "endpoint": "/api/v1/a2a/message", "skills": AGENT_CARDS}


@router.post("/a2a/message")
def a2a_message(request: A2AMessageRequest) -> dict[str, object]:
    """사용자가 지정한 전문 에이전트에 메시지를 직접 위임합니다."""
    try:
        # 전문 에이전트 호출 결과를 그대로 반환합니다.
        return invoke_specialist(request.agent_name, request.message, request.provider)
    except Exception as error:
        # 등록되지 않은 에이전트나 처리 실패를 400 오류로 반환합니다.
        raise HTTPException(status_code=400, detail=f"{type(error).__name__}: {error}") from error


@router.get("/data/files")
def data_files() -> list[dict[str, object]]:
    """원본 프로젝트에서 유지된 전체 데이터 파일을 반환합니다."""
    # 데이터 서비스의 파일 목록을 반환합니다.
    return list_data_files()


@router.post("/rag/reset")
def rag_reset() -> dict[str, str]:
    """공급자별 메모리 FAISS 인덱스를 초기화합니다."""
    # RAG 캐시를 비웁니다.
    reset_rag()
    # 초기화 성공 메시지를 반환합니다.
    return {"status": "reset"}


@router.get("/reports/{filename}")
def download_report(filename: str):
    """reports 폴더에서 생성된 보고서 또는 차트 파일을 다운로드합니다."""
    # 경로 이동 공격을 막기 위해 파일명 부분만 사용합니다.
    safe_name = Path(filename).name
    # 보고서 폴더 내부의 실제 파일 경로를 계산합니다.
    path = REPORTS_DIR / safe_name
    # 파일이 없으면 404 오류를 반환합니다.
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    # 브라우저가 다운로드할 수 있도록 파일 응답을 반환합니다.
    return FileResponse(path)
