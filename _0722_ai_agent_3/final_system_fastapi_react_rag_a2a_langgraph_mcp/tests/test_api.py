# -*- coding: utf-8 -*-
"""FastAPI의 API 키 비의존 엔드포인트 테스트입니다."""

# TestClient는 실제 서버를 띄우지 않고 FastAPI 요청을 테스트합니다.
from fastapi.testclient import TestClient

# FastAPI 앱 객체를 가져옵니다.
from app.main import app

# client는 각 테스트에서 재사용할 HTTP 테스트 클라이언트입니다.
client = TestClient(app)


# test_health는 상태 확인 API가 정상인지 검증합니다.
def test_health() -> None:
    """GET /api/v1/health는 HTTP 200과 ok 상태를 반환해야 합니다."""
    # 상태 확인 엔드포인트를 호출합니다.
    response = client.get("/api/v1/health")
    # HTTP 상태 코드가 성공인지 확인합니다.
    assert response.status_code == 200
    # JSON의 status 필드가 ok인지 확인합니다.
    assert response.json()["status"] == "ok"


# test_tool_call은 MCP 호환 로컬 도구 API를 검증합니다.
def test_tool_call() -> None:
    """없는 주문번호 도구 호출이 안전한 실패 결과를 반환해야 합니다."""
    # 주문 도구 호출 요청을 보냅니다.
    response = client.post(
        "/api/v1/tools/call",
        json={"tool_name": "get_order_status", "arguments": {"order_id": "O999999"}},
    )
    # API 자체는 정상 처리되므로 HTTP 200이어야 합니다.
    assert response.status_code == 200
    # 결과에 찾을 수 없다는 문구가 포함되어야 합니다.
    assert "찾을 수 없습니다" in response.json()["result"]
