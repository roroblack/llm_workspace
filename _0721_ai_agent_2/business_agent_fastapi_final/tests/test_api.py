# -*- coding: utf-8 -*-
"""LLM 호출 없이 확인 가능한 FastAPI 기본 엔드포인트 테스트입니다."""

# FastAPI 테스트 클라이언트를 가져옵니다.
from fastapi.testclient import TestClient
# 실제 애플리케이션 객체를 가져옵니다.
from app.main import app

# 테스트 요청에 사용할 클라이언트를 생성합니다.
client = TestClient(app)


def test_health() -> None:
    """헬스 체크가 정상 상태와 전체 아키텍처를 반환하는지 확인합니다."""
    # 헬스 체크 API를 호출합니다.
    response = client.get("/api/v1/health")
    # HTTP 상태 코드가 200인지 확인합니다.
    assert response.status_code == 200
    # 응답 JSON에 LangGraph가 포함되는지 확인합니다.
    assert "LangGraph" in response.json()["architecture"]


def test_mcp_monthly_sales_tool() -> None:
    """HTTP MCP 호환 월별 매출 도구가 API 키 없이 동작하는지 확인합니다."""
    # 특정 월 매출 도구를 호출합니다.
    response = client.post("/api/v1/tools/call", json={"tool_name": "monthly_sales", "month": "2026-05", "filename": "monthly_sales.csv", "limit": 10})
    # HTTP 상태 코드가 200인지 확인합니다.
    assert response.status_code == 200
    # 결과 문자열에 대상 월이 포함되는지 확인합니다.
    assert "2026-05" in response.json()["result"]


def test_prompt_lab_validation() -> None:
    """Prompt 실습 요청 스키마가 잘못된 파라미터를 거부하는지 확인합니다."""
    # temperature 범위를 벗어난 요청은 422 검증 오류가 되어야 합니다.
    over_range = client.post("/api/v1/prompt-lab", json={"message": "hi", "temperature": 5})
    assert over_range.status_code == 422
    # message 가 비어 있으면 검증 오류가 되어야 합니다.
    empty_message = client.post("/api/v1/prompt-lab", json={"message": ""})
    assert empty_message.status_code == 422


def test_prompt_lab_message_builder() -> None:
    """few-shot 및 지시문이 메시지 구성에 반영되는지 API 키 없이 확인합니다."""
    # 메시지 구성 함수를 직접 가져옵니다.
    from app.services.prompt_lab_service import _build_messages
    # few-shot 을 켜고 System Prompt·지시문·질문을 전달합니다.
    messages = _build_messages("역할 지정", "지시문", "질문 본문", few_shot=True)
    # System + few-shot 2쌍(4개) + 실제 질문 1개 = 총 6개 메시지여야 합니다.
    assert len(messages) == 6
    # 마지막 사용자 메시지에는 지시문과 질문이 함께 담겨야 합니다.
    assert "지시문" in messages[-1].content and "질문 본문" in messages[-1].content
