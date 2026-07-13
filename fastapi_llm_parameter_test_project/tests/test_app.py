# -*- coding: utf-8 -*-
"""FastAPI 앱 기본 동작 테스트입니다."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_ui_page():
    """루트 경로가 HTML UI 페이지를 반환하는지 확인합니다."""

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "LLM API 실습 테스트 앱" in response.text


def test_health_check():
    """서버 상태 확인 API가 정상 응답하는지 확인합니다."""

    response = client.get("/api/system/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
