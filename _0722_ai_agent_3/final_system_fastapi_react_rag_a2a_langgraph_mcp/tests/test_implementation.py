# -*- coding: utf-8 -*-
"""구현 과제의 문의 연계와 보고서 기능 회귀 테스트입니다."""

from fastapi.testclient import TestClient

from app.api import routes
from app.main import app
from app.services import report_service
from app.services.complaint_service import HANDOFF_ANSWER, infer_department, is_action_complaint

client = TestClient(app)


def test_action_complaint_detection_distinguishes_policy_question() -> None:
    assert is_action_complaint("주문한 상품을 교환해 주세요") is True
    assert is_action_complaint("환불해 주세요") is True
    assert is_action_complaint("환불 절차를 알려 주세요") is False
    assert infer_department("환불해 주세요") == "CS_REFUND"


def test_chat_action_request_is_saved_before_llm(monkeypatch) -> None:
    def fake_save(custum_id: str, message: str, dept_id: str | None = None) -> dict[str, object]:
        return {
            "answer": HANDOFF_ANSWER,
            "cc_id": 17,
            "custum_id": custum_id,
            "dept_id": dept_id or "CS_EXCHANGE",
            "receipt_status": False,
            "resolution_status": False,
            "inquiry_date": "2026-07-22T15:00:00.000000",
        }

    monkeypatch.setattr(routes, "create_customer_complaint", fake_save)
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "상품을 교환해 주세요",
            "thread_id": "CUST-1",
            "provider": "openai",
        },
    )
    assert response.status_code == 200
    assert response.json()["answer"] == HANDOFF_ANSWER
    assert response.json()["route"] == "complaint"
    assert response.json()["complaint_id"] == 17


def test_reports_use_safe_fallback_without_llm(monkeypatch, tmp_path) -> None:
    def fail_model(_provider: str):
        raise RuntimeError("API key unavailable")

    monkeypatch.setattr(report_service, "REPORTS_DIR", tmp_path)
    monkeypatch.setattr(report_service, "create_chat_model", fail_model)

    summary = report_service.generate_summary_report(
        "테스트 요약",
        "첫 번째 사실입니다. 두 번째 사실입니다. 후속 조치를 확인합니다.",
        "openai",
    )
    sales = report_service.generate_sales_report("2026-05", "openai")

    assert summary["used_fallback"] is True
    assert (tmp_path / str(summary["report_path"])).exists()
    assert sales["used_fallback"] is True
    assert sales["facts"]["month"] == "2026-05"
    assert (tmp_path / str(sales["report_path"])).exists()
