# -*- coding: utf-8 -*-
"""
FastAPI API 라우터입니다.
화면과 Swagger에서 호출할 수 있는 API 엔드포인트를 정의합니다.
"""

# APIRouter는 여러 API 경로를 모듈 단위로 묶기 위해 사용합니다.
from fastapi import APIRouter

# 설정 객체를 가져옵니다.
from app.core.config import settings

# 요청/응답 스키마를 가져옵니다.
from app.schemas import (
    AgentResponse,
    QuestionRequest,
    StatusResponse,
    VectorSearchRequest,
    VectorSearchResponse,
)

# Torch 분석 서비스를 가져옵니다.
from app.services.torch_service import analyze_inventory_with_torch

# Vector DB 서비스를 가져옵니다.
from app.services.vector_db import rebuild_vector_db, search_vector_db

# ReAct 에이전트 서비스를 가져옵니다.
from app.services.react_agent import run_openai_react_agent

# Gemini 보조 응답 서비스를 가져옵니다.
from app.services.gemini_service import ask_gemini_with_context

# 도구 함수를 가져옵니다.
from app.services.tools_service import get_price, get_stock, get_reorder_level, get_order_status, search_knowledge_base


# API 라우터 객체를 생성합니다.
router = APIRouter(prefix="/api", tags=["api"])


@router.get("/health", response_model=StatusResponse)
def health() -> StatusResponse:
    """서버와 환경 설정 상태를 확인합니다."""
    # 서버 상태와 API 키 준비 여부를 반환합니다.
    return StatusResponse(
        ok=True,
        message="FastAPI 서버가 정상 실행 중입니다.",
        details=settings.model_dump(),
    )


@router.post("/vector/rebuild")
def rebuild_vector_store() -> dict:
    """data/docs 문서를 다시 임베딩하여 Vector DB를 재생성합니다."""
    # Vector DB 재생성 결과를 반환합니다.
    return rebuild_vector_db()


@router.post("/vector/search", response_model=VectorSearchResponse)
def vector_search(request: VectorSearchRequest) -> VectorSearchResponse:
    """Vector DB에서 질문과 관련된 문서를 검색합니다."""
    # 검색 결과를 가져옵니다.
    items = search_vector_db(request.query, request.top_k)

    # 응답 스키마로 반환합니다.
    return VectorSearchResponse(items=items)


@router.get("/torch/stock-summary")
def stock_summary() -> dict:
    """Torch 텐서 연산으로 재고/재주문 요약을 계산합니다."""
    # Torch 분석 결과를 반환합니다.
    return analyze_inventory_with_torch()


@router.post("/react/openai", response_model=AgentResponse)
def react_openai(request: QuestionRequest) -> AgentResponse:
    """OpenAI + LangChain Tools 기반 ReAct 에이전트를 실행합니다."""
    # ReAct 에이전트를 실행하고 결과를 반환합니다.
    return run_openai_react_agent(request.question, request.max_steps)


@router.post("/gemini/ask")
def gemini_ask(request: QuestionRequest) -> dict:
    """Vector DB 검색 결과를 참고 문맥으로 넣어 Gemini API에 질문합니다."""
    # Gemini 응답을 생성합니다.
    answer = ask_gemini_with_context(request.question)

    # 응답을 dict로 반환합니다.
    return {"answer": answer}


@router.get("/tools/local-demo")
def local_tools_demo() -> dict:
    """API 키 없이도 도구 함수 동작을 확인하는 로컬 데모입니다."""
    # 여러 도구를 직접 실행해 결과를 확인합니다.
    return {
        "price": get_price.invoke({"product_name": "이어버드"}),
        "stock": get_stock.invoke({"product_name": "스마트워치"}),
        "reorder_level": get_reorder_level.invoke({"product_name": "스마트워치"}),
        "order": get_order_status.invoke({"order_id": "O000106"}),
        "knowledge": search_knowledge_base.invoke({"query": "ReAct Agent Loop 안전장치"}),
    }
