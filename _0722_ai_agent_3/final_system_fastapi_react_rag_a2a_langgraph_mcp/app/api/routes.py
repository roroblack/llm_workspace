# -*- coding: utf-8 -*-
"""FastAPI REST 엔드포인트를 정의하는 라우터 모듈입니다."""

# time은 API 응답 시간을 측정합니다.
import time

# APIRouter는 큰 FastAPI 앱을 기능별 파일로 분리합니다.
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

# A2A 에이전트 카드와 위임 함수를 가져옵니다.
from app.agents.specialists import delegate_to_agent, list_agent_cards
# 환경설정과 데이터 목록 서비스를 가져옵니다.
from app.core.settings import get_settings
# 요청 및 응답 스키마를 가져옵니다.
from app.models.schemas import (
    A2AMessageRequest,
    ChatRequest,
    ChatResponse,
    ComplaintRequest,
    ComplaintResponse,
    ReportResponse,
    SalesReportRequest,
    SummaryReportRequest,
    ToolRequest,
    ToolResponse,
)
# 통합 LangGraph 실행 함수를 가져옵니다.
from app.graph.workflow import run_workflow
# MCP 로컬 호출 함수를 가져옵니다.
from app.mcp_server.client import call_local_mcp_tool
# 데이터 파일 목록과 RAG 캐시 초기화 함수를 가져옵니다.
from app.services.data_service import list_data_files
from app.services.rag_service import reset_rag_cache
from app.services.complaint_service import create_customer_complaint, is_action_complaint
from app.services.report_service import generate_sales_report, generate_summary_report, resolve_report_path

# router는 /api/v1 아래에 등록될 API 라우터 객체입니다.
router = APIRouter(prefix="/api/v1", tags=["Final System Agent"])


# health 엔드포인트는 서버와 API 키 설정 상태를 확인합니다.
@router.get("/health")
def health() -> dict[str, object]:
    """애플리케이션 상태와 공급자별 API 키 설정 여부를 반환합니다."""
    # 현재 환경설정을 읽습니다.
    settings = get_settings()
    # 실제 키 문자열은 노출하지 않고 존재 여부만 반환합니다.
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "openai_key_configured": bool(settings.openai_api_key),
        "gemini_key_configured": bool(settings.google_api_key),
    }


# chat 엔드포인트는 전체 ReAct-RAG-A2A-LangGraph-MCP 흐름을 실행합니다.
@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """사용자 질문을 통합 LangGraph 워크플로우로 처리합니다."""
    # 워크플로우 실행 시작 시간을 기록합니다.
    started_at = time.perf_counter()
    # 실행성 교환·환불 문의는 LLM 호출 전에 담당 부서 큐에 확실히 저장합니다.
    if is_action_complaint(request.message):
        try:
            complaint = create_customer_complaint(
                custum_id=request.custum_id or request.thread_id,
                message=request.message,
                dept_id=request.dept_id,
            )
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"담당 부서 문의 저장에 실패했습니다: {exc}") from exc
        return ChatResponse(
            answer=str(complaint["answer"]),
            provider=request.provider,
            thread_id=request.thread_id,
            route="complaint",
            complaint_id=int(complaint["cc_id"]),
            trace=[
                {"stage": "Complaint", "detail": f"customer_complaint 저장 완료: cc_id={complaint['cc_id']}"},
                {"stage": "Complete", "detail": f"총 처리시간={time.perf_counter() - started_at:.3f}초"},
            ],
        )
    # 요청 스키마 값을 그래프 실행 함수에 전달합니다.
    result = run_workflow(request.message, request.thread_id, request.provider)
    # 최종 답변이 없으면 안전한 기본 메시지를 사용합니다.
    answer = result.get("answer", "답변을 생성하지 못했습니다.")
    # 기존 trace 목록을 복사합니다.
    trace = list(result.get("trace", []))
    # 전체 처리 시간을 마지막 추적 단계로 추가합니다.
    trace.append({"stage": "Complete", "detail": f"총 처리시간={time.perf_counter() - started_at:.3f}초"})
    # Pydantic 응답 모델로 검증된 JSON 결과를 반환합니다.
    return ChatResponse(
        answer=str(answer),
        provider=request.provider,
        thread_id=request.thread_id,
        route=str(result.get("route", "error")),
        trace=trace,
    )


@router.post("/complaints/connect", response_model=ComplaintResponse)
def connect_complaint(request: ComplaintRequest) -> ComplaintResponse:
    """교환·환불 실행 문의를 MySQL 담당 부서 큐에 등록합니다."""
    if not is_action_complaint(request.message):
        raise HTTPException(
            status_code=400,
            detail="교환·환불·반품을 실제로 요청하는 문장을 입력해 주세요. 예: 환불해 주세요.",
        )
    try:
        result = create_customer_complaint(request.custum_id, request.message, request.dept_id)
        return ComplaintResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"MySQL 문의 저장에 실패했습니다: {exc}") from exc


@router.post("/reports/summary", response_model=ReportResponse)
def create_summary_report(request: SummaryReportRequest) -> ReportResponse:
    """입력 텍스트를 map-reduce 방식으로 요약해 보고서를 생성합니다."""
    try:
        return ReportResponse(**generate_summary_report(request.title, request.text, request.provider))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"요약 보고서 생성에 실패했습니다: {exc}") from exc


@router.post("/reports/sales", response_model=ReportResponse)
def create_sales_report(request: SalesReportRequest) -> ReportResponse:
    """월간 CSV 확정 수치로 임원용 매출 보고서를 생성합니다."""
    try:
        return ReportResponse(**generate_sales_report(request.month, request.provider))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"매출 보고서 생성에 실패했습니다: {exc}") from exc


@router.get("/reports/{filename}")
def download_report(filename: str):
    """생성된 마크다운 보고서를 안전하게 다운로드합니다."""
    try:
        path = resolve_report_path(filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="보고서 파일을 찾을 수 없습니다.")
    return FileResponse(path, media_type="text/markdown; charset=utf-8", filename=path.name)


# tools 엔드포인트는 MCP와 같은 규칙으로 개별 도구를 테스트합니다.
@router.post("/tools/call", response_model=ToolResponse)
def call_tool(request: ToolRequest) -> ToolResponse:
    """주문, 재고, FAQ, 교환 도구를 LLM 없이 직접 실행합니다."""
    # 잘못된 인자 구조를 HTTP 400으로 변환하기 위해 예외를 처리합니다.
    try:
        # 도구 이름과 인자를 로컬 MCP 클라이언트에 전달합니다.
        result = call_local_mcp_tool(request.tool_name, request.arguments)
        # 성공 응답 모델을 반환합니다.
        return ToolResponse(success=True, tool_name=request.tool_name, result=result)
    except TypeError as exc:
        # 필수 인자 누락 또는 잘못된 인자 이름을 상세히 안내합니다.
        raise HTTPException(status_code=400, detail=f"도구 인자가 올바르지 않습니다: {exc}") from exc


# agent_cards 엔드포인트는 A2A 에이전트 발견 정보를 제공합니다.
@router.get("/a2a/agents")
def agent_cards() -> dict[str, object]:
    """현재 서비스가 제공하는 A2A 전문 에이전트 카드를 반환합니다."""
    # 카드 목록을 agents 키로 감싸 반환합니다.
    return {"agents": list_agent_cards()}


# a2a_message 엔드포인트는 특정 전문 에이전트에 직접 작업을 위임합니다.
@router.post("/a2a/message")
def a2a_message(request: A2AMessageRequest) -> dict[str, object]:
    """대상 에이전트 이름을 지정하여 A2A 위임 결과를 확인합니다."""
    # 전문 에이전트 게이트웨이에 메시지를 전달합니다.
    result = delegate_to_agent(request.target_agent, request.message, request.provider)
    # A2A 메시지 응답에 대상과 세션 정보를 포함합니다.
    return {
        "target_agent": request.target_agent,
        "thread_id": request.thread_id,
        "provider": request.provider,
        "result": result,
    }


# data_files 엔드포인트는 프로젝트에 포함된 실데이터를 확인합니다.
@router.get("/data/files")
def data_files() -> dict[str, object]:
    """data.zip에서 추출된 전체 파일명과 크기를 반환합니다."""
    # 파일 목록을 files 키로 감싸 반환합니다.
    return {"files": list_data_files()}


# reset_rag 엔드포인트는 정책 문서 변경 후 인덱스를 초기화합니다.
@router.post("/rag/reset")
def reset_rag() -> dict[str, str]:
    """메모리의 공급자별 FAISS 인덱스를 삭제합니다."""
    # 캐시된 벡터 인덱스를 제거합니다.
    reset_rag_cache()
    # 다음 정책 요청에서 다시 생성된다는 안내를 반환합니다.
    return {"message": "RAG 캐시를 초기화했습니다. 다음 정책 요청에서 다시 인덱싱합니다."}


# exercise_exchange는 실습문제 1 해답을 API로 실행합니다.
@router.post("/exercises/exchange", response_model=ToolResponse)
def exercise_exchange(request: ToolRequest) -> ToolResponse:
    """교환신청 쓰기 도구 실습 해답을 실행합니다."""
    # 교환 도구가 아닌 요청은 잘못된 실습 호출로 처리합니다.
    if request.tool_name != "request_exchange":
        # 올바른 tool_name을 안내하는 HTTP 400 오류를 발생시킵니다.
        raise HTTPException(status_code=400, detail="tool_name은 request_exchange여야 합니다.")
    # 공통 MCP 호출 계층으로 교환 도구를 실행합니다.
    result = call_local_mcp_tool(request.tool_name, request.arguments)
    # 실습 실행 결과를 반환합니다.
    return ToolResponse(success=True, tool_name=request.tool_name, result=result)


# exercise_memory는 서로 다른 thread_id의 메모리 격리 테스트 방법을 반환합니다.
@router.get("/exercises/memory")
def exercise_memory() -> dict[str, object]:
    """실습문제 2의 세션 메모리 격리 테스트 시나리오를 제공합니다."""
    # 두 사용자에 대해 서로 다른 thread_id를 사용하도록 시나리오를 반환합니다.
    return {
        "description": "동일 provider로 /chat을 호출하되 user-a와 user-b에 서로 다른 thread_id를 사용합니다.",
        "scenario": [
            {"thread_id": "user-a", "message": "환불 절차 알려줘"},
            {"thread_id": "user-b", "message": "내가 아까 물어본 정책이 뭐였지?"},
            {"thread_id": "user-a", "message": "아까 그 정책 다시 알려줘"},
        ],
        "expected": "user-a만 환불 맥락을 기억하고 user-b는 맥락이 없다고 답해야 합니다.",
    }
