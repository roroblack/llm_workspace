"""A2A(Agent-to-Agent) — 에이전트 발견(카드) + 전문 에이전트 위임.

무폴백 확인: 미등록 에이전트·필수 식별자 누락은 문자열이 아니라 422(ValidationErr).
위임은 기존 서비스(commerce_tools/rag/recommend)를 재사용한다(중복 구현 아님).
"""

from __future__ import annotations

_EXPECTED_AGENTS = {"order-agent", "catalog-agent", "knowledge-agent", "recommend-agent"}


def test_agent_cards_discovery(client):
    r = client.get("/api/a2a/agents")
    assert r.status_code == 200
    cards = r.json()["agents"]
    assert {c["name"] for c in cards} == _EXPECTED_AGENTS
    for c in cards:  # 카드 필수 필드(발견 계약)
        assert c["skills"] and c["description"]
        assert c["endpoint"] == "/api/a2a/message"
        assert c["version"] == "1.0.0"


def test_delegate_catalog_agent_by_product_code(client):
    """catalog-agent + 상품코드 → get_stock 재사용(시드된 P0001)."""
    r = client.post("/api/a2a/message", json={"target_agent": "catalog-agent", "message": "P0001 재고 알려줘"})
    assert r.status_code == 200
    result = r.json()["result"]
    assert result["ok"] is True and "stock" in result


def test_delegate_catalog_agent_price_intent(client):
    """catalog-agent가 광고한 '가격 조회' 능력 — 가격 의도면 get_price로 분기(카드-실행 일치)."""
    r = client.post("/api/a2a/message", json={"target_agent": "catalog-agent", "message": "P0001 가격 얼마야"})
    assert r.status_code == 200
    result = r.json()["result"]
    assert result["ok"] is True and "price" in result


def test_card_and_handler_registries_do_not_drift():
    """카드와 핸들러 레지스트리는 항상 동일 집합이어야 한다(import 시 fail-fast의 정적 확인)."""
    from app.a2a.cards import AGENT_CARDS
    from app.a2a.gateway import _HANDLERS

    assert set(AGENT_CARDS) == set(_HANDLERS)


def test_delegate_catalog_agent_by_keyword(client):
    r = client.post("/api/a2a/message", json={"target_agent": "catalog-agent", "message": "이어버드"})
    assert r.status_code == 200
    result = r.json()["result"]
    assert result["ok"] is True and "results" in result


def test_delegate_order_agent_routes_to_order_status(client):
    """order-agent + 주문번호 → get_order_status 재사용. 없는 주문은 구조화 관찰(폴백 아님)."""
    r = client.post("/api/a2a/message", json={"target_agent": "order-agent", "message": "주문 O999999 상태"})
    assert r.status_code == 200
    result = r.json()["result"]
    assert result["ok"] is False and result["error_code"] == "order_not_found"


def test_order_agent_missing_order_number_is_422(client):
    """주문번호 누락은 무폴백 — 문자열 안내가 아니라 422 ValidationErr."""
    r = client.post("/api/a2a/message", json={"target_agent": "order-agent", "message": "내 주문 어디쯤이야"})
    assert r.status_code == 422


def test_unknown_agent_is_422_not_string_fallback(client):
    """미등록 에이전트는 문자열 반환(참조 구현의 폴백)이 아니라 422여야 한다."""
    r = client.post("/api/a2a/message", json={"target_agent": "no-such-agent", "message": "안녕"})
    assert r.status_code == 422


def test_delegate_knowledge_agent_reuses_rag_search(client, monkeypatch):
    """knowledge-agent → rag_service.search 재사용(라우팅 결정 검증, 무거운 인덱스 없이 스텁)."""
    monkeypatch.setattr("app.rag.service.search", lambda q: [{"text": "정책", "score": 0.9}])
    r = client.post("/api/a2a/message", json={"target_agent": "knowledge-agent", "message": "환불 정책"})
    assert r.status_code == 200
    result = r.json()["result"]
    assert result["ok"] is True and result["count"] == 1


def test_delegate_recommend_agent_reuses_recommender(client, monkeypatch):
    """recommend-agent → ml.recommend.recommend_products 재사용(스텁으로 라우팅만 검증)."""
    monkeypatch.setattr(
        "app.ml.recommend.recommend_products",
        lambda db, query, **kw: {"ok": True, "query": query, "items": []},
    )
    r = client.post("/api/a2a/message", json={"target_agent": "recommend-agent", "message": "겨울 전자제품"})
    assert r.status_code == 200
    assert r.json()["result"]["ok"] is True


def test_a2a_is_ops_only_separated_from_customer():
    """A2A는 운영/통합 표면 — 고객 공개 포트(customer_app)에는 없어야(404) 하고 운영 앱엔 있어야."""
    from fastapi.testclient import TestClient

    from app.main import admin_app, customer_app

    cust = TestClient(customer_app)
    adm = TestClient(admin_app)
    assert cust.get("/api/a2a/agents").status_code == 404
    assert cust.post("/api/a2a/message", json={"target_agent": "order-agent", "message": "x"}).status_code == 404
    assert adm.get("/api/a2a/agents").status_code == 200
