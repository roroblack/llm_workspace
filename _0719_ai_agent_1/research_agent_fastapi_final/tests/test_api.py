# -*- coding: utf-8 -*-
"""외부 LLM 호출 없이 확인 가능한 FastAPI 기본 엔드포인트 테스트입니다."""

# FastAPI 테스트 클라이언트를 가져옵니다.
from fastapi.testclient import TestClient
# 실제 애플리케이션 객체를 가져옵니다.
from app.main import app
from app.mcp_server import tools as mcp_tools

# 테스트에서 재사용할 클라이언트 객체를 생성합니다.
client = TestClient(app)


def test_health() -> None:
    """상태 확인 엔드포인트가 정상 응답하는지 검사합니다."""
    # health API를 호출합니다.
    response = client.get("/api/v1/health")
    # HTTP 200 상태인지 확인합니다.
    assert response.status_code == 200
    # JSON 상태 값이 ok인지 확인합니다.
    assert response.json()["status"] == "ok"


def test_agent_cards() -> None:
    """A2A 전문 에이전트 카드가 공개되는지 검사합니다."""
    # 카드 목록 API를 호출합니다.
    response = client.get("/api/v1/a2a/agents")
    # 요청이 성공했는지 확인합니다.
    assert response.status_code == 200
    # 다섯 개 전문 에이전트가 등록됐는지 확인합니다.
    assert len(response.json()) == 5


def test_exercises() -> None:
    """두 실습 해답 실행 정보가 유지되는지 검사합니다."""
    # 실습 정보 API를 호출합니다.
    response = client.get("/api/v1/exercises")
    # 정상 응답인지 확인합니다.
    assert response.status_code == 200
    # 실습문제 1과 2가 모두 포함됐는지 확인합니다.
    assert {"exercise_1", "exercise_2"}.issubset(response.json())


def test_mysql_tool_endpoint(monkeypatch) -> None:
    """DB 저장 버튼이 사용하는 MCP 호환 HTTP 도구 경로를 검사합니다."""
    monkeypatch.setattr(
        mcp_tools,
        "save_report_to_mysql",
        lambda topic, result, result_time: {
            "saved": True,
            "table": "REPORT",
            "topic": str(topic),
            "result_time": str(result_time),
        },
    )
    response = client.post(
        "/api/v1/tools/call",
        json={
            "tool_name": "save_report_mysql",
            "arguments": {
                "topic": "테스트 주제",
                "result": "테스트 답변",
                "result_time": "2026-07-20T08:30:45Z",
            },
        },
    )
    assert response.status_code == 200
    assert response.json()["saved"] is True
    assert response.json()["table"] == "REPORT"


def test_index_contains_mysql_save_button() -> None:
    """최종 답변 영역에 DB 저장 버튼이 렌더링되는지 검사합니다."""
    response = client.get("/")
    assert response.status_code == 200
    assert 'id="save-db"' in response.text
    assert "DB에 저장" in response.text
