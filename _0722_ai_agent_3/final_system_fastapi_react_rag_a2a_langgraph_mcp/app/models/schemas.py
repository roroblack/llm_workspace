# -*- coding: utf-8 -*-
"""FastAPI 요청 및 응답에 사용하는 Pydantic 스키마 모듈입니다."""

# typing.Any는 실행 추적 정보처럼 다양한 타입의 값을 허용합니다.
from typing import Any, Literal

# BaseModel은 JSON 요청과 응답을 검증하는 기본 클래스입니다.
from pydantic import BaseModel, Field


# ChatRequest는 통합 에이전트 질문 API의 입력 구조입니다.
class ChatRequest(BaseModel):
    """사용자 질문과 세션 정보를 전달하는 요청 모델입니다."""

    # message는 에이전트가 처리할 자연어 질문입니다.
    message: str = Field(min_length=1, description="사용자 질문")
    # thread_id는 LangGraph 메모리에서 대화 세션을 구분합니다.
    thread_id: str = Field(default="web-user", min_length=1, description="대화 세션 ID")
    # provider는 이번 요청에서 사용할 LLM 공급자입니다.
    provider: Literal["openai", "gemini"] = Field(default="openai")
    # 실행성 교환·환불 요청을 DB에 저장할 때 사용할 고객 식별자입니다.
    custum_id: str | None = Field(default=None, max_length=100)
    # 화면에서 담당 부서를 지정하지 않으면 문의 유형에 따라 자동 결정합니다.
    dept_id: str | None = Field(default=None, max_length=50)


# ChatResponse는 최종 답변과 워크플로우 실행 정보를 반환합니다.
class ChatResponse(BaseModel):
    """통합 워크플로우의 최종 결과 모델입니다."""

    # answer는 사용자에게 보여 줄 최종 한국어 답변입니다.
    answer: str
    # provider는 실제 사용된 모델 공급자입니다.
    provider: str
    # thread_id는 응답이 속한 대화 세션입니다.
    thread_id: str
    # route는 분류기가 선택한 처리 경로입니다.
    route: str
    # trace는 ReAct, RAG, A2A, LangGraph, MCP 단계 실행 기록입니다.
    trace: list[dict[str, Any]] = Field(default_factory=list)
    # 실행성 문의가 저장된 경우 생성된 customer_complaint 기본키입니다.
    complaint_id: int | None = None


class ComplaintRequest(BaseModel):
    """담당 부서로 전달할 고객 문의 요청입니다."""

    message: str = Field(min_length=1, max_length=5000)
    custum_id: str = Field(min_length=1, max_length=100)
    dept_id: str | None = Field(default=None, max_length=50)


class ComplaintResponse(BaseModel):
    """문의 저장 결과와 고객 안내 문구입니다."""

    answer: str
    cc_id: int
    custum_id: str
    dept_id: str
    receipt_status: bool = False
    resolution_status: bool = False
    inquiry_date: str


class SummaryReportRequest(BaseModel):
    """요약 보고서 생성 요청입니다."""

    title: str = Field(default="요약 보고서", min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=100_000)
    provider: Literal["openai", "gemini"] = Field(default="openai")


class SalesReportRequest(BaseModel):
    """임원용 월간 매출 보고서 생성 요청입니다."""

    month: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}$")
    provider: Literal["openai", "gemini"] = Field(default="openai")


class ReportResponse(BaseModel):
    """생성된 보고서 내용과 다운로드 경로입니다."""

    title: str
    content: str
    report_path: str
    download_url: str
    used_fallback: bool = False
    facts: dict[str, Any] | None = None


# ToolRequest는 개별 데이터 도구 테스트에 사용하는 공통 입력 모델입니다.
class ToolRequest(BaseModel):
    """도구 이름과 도구 인자를 전달하는 요청 모델입니다."""

    # tool_name은 실행할 도구의 고유 이름입니다.
    tool_name: Literal["get_order_status", "get_stock", "search_faq", "request_exchange"]
    # arguments는 각 도구에 필요한 키-값 인자입니다.
    arguments: dict[str, Any] = Field(default_factory=dict)


# ToolResponse는 MCP 또는 로컬 도구 실행 결과를 반환합니다.
class ToolResponse(BaseModel):
    """도구 실행 결과와 오류 상태를 반환하는 모델입니다."""

    # success는 도구 실행 성공 여부입니다.
    success: bool
    # tool_name은 실행한 도구 이름입니다.
    tool_name: str
    # result는 도구가 생성한 문자열 결과입니다.
    result: str


# A2AMessageRequest는 에이전트 간 위임 메시지를 표현합니다.
class A2AMessageRequest(BaseModel):
    """A2A 게이트웨이에 전달하는 에이전트 메시지 모델입니다."""

    # target_agent는 작업을 받을 전문 에이전트 이름입니다.
    target_agent: Literal["order-agent", "inventory-agent", "faq-agent", "policy-agent", "exchange-agent"]
    # message는 전문 에이전트가 처리할 사용자 요청입니다.
    message: str = Field(min_length=1)
    # provider는 전문 에이전트가 사용할 LLM 공급자입니다.
    provider: Literal["openai", "gemini"] = Field(default="openai")
    # thread_id는 에이전트 간에도 동일하게 유지할 세션 ID입니다.
    thread_id: str = Field(default="a2a-user")
