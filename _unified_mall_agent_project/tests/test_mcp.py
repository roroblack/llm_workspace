"""MCP 서버 결정론 테스트 — 등록 + 도구 로직(LLM/subprocess 불필요).

FastMCP 인스턴스를 **인프로세스**로 호출한다(`mcp.call_tool`은 (blocks, structured)
튜플 반환). 커머스/ML(규칙) 도구는 실 DB로 결정론적. LLM/모델 로드 도구는 여기서
검증하지 않는다(각각 @llm/@ml, 스모크는 test_mcp_stdio).

프로젝트에 async 테스트 플러그인이 없으므로 코루틴은 asyncio.run으로 구동한다.
"""

from __future__ import annotations

import asyncio
import json

import pytest

from app.mcp import server as mcp_server
from app.mcp.server import mcp


def _run(coro):
    return asyncio.run(coro)


# 계획 합의: 도구는 정확히 10개(커머스5 + RAG2 + ML3), search_knowledge_base 제외
EXPECTED_TOOLS = {
    "get_price",
    "get_stock",
    "get_order_status",
    "search_product",
    "get_exchange_rate",
    "vector_search",
    "rag_qa",
    "analyze_sentiment",
    "classify_intent",
    "recommend_products",
}


def test_registered_tools_exact_set():
    tools = _run(mcp.list_tools())
    names = {t.name for t in tools}
    assert names == EXPECTED_TOOLS
    assert "search_knowledge_base" not in names  # vector_search와 중복이라 제외


def test_registered_resources_and_prompt():
    resources = _run(mcp.list_resources())
    uris = {str(r.uri) for r in resources}
    assert uris == {"config://runtime", "catalog://products"}
    prompts = _run(mcp.list_prompts())
    assert {p.name for p in prompts} == {"grounded_rag_prompt"}


def test_get_price_tool_via_mcp():
    _blocks, structured = _run(mcp.call_tool("get_price", {"product_code": "P0001"}))
    assert structured["ok"] is True
    assert structured["price"] > 0


def test_get_price_not_found_is_structured_fail():
    _blocks, structured = _run(mcp.call_tool("get_price", {"product_code": "NOPE"}))
    assert structured["ok"] is False
    assert structured["error_code"] == "product_not_found"


def test_get_exchange_rate_no_session_needed():
    _blocks, structured = _run(mcp.call_tool("get_exchange_rate", {"currency": "usd"}))
    assert structured["ok"] is True
    assert structured["currency"] == "USD"
    assert structured["rate"] > 0


def test_get_exchange_rate_unsupported():
    _blocks, structured = _run(mcp.call_tool("get_exchange_rate", {"currency": "XXX"}))
    assert structured["ok"] is False
    assert structured["error_code"] == "currency_not_supported"


def test_classify_intent_tool_via_mcp():
    # 규칙 기반 → 모델 로드 불필요 → 결정론
    _blocks, structured = _run(mcp.call_tool("classify_intent", {"text": "환불하고 싶어요"}))
    assert "intent" in structured


def test_runtime_config_resource():
    content = _run(mcp.read_resource("config://runtime"))
    items = list(content)
    payload = json.loads(items[0].content)
    assert payload["llm_provider"] in {"local", "openai", "gemini"}
    serialized = json.dumps(payload)
    # 실제 비밀 값이 새지 않아야 한다: conftest가 설정한 SECRET_KEY 센티널이 없어야 한다
    assert "test-secret-key-do-not-use-in-prod" not in serialized
    # 비밀 성격 필드명도 없어야 한다
    low = serialized.lower()
    assert "api_key" not in low
    assert "secret" not in low


def test_catalog_resource_lists_products():
    content = _run(mcp.read_resource("catalog://products"))
    items = list(content)
    payload = json.loads(items[0].content)
    assert payload["count"] > 0
    assert payload["products"][0]["product_code"].startswith("P")


# --- FastMCP 계약(메타데이터) 검증 ---------------------------------------
def test_resource_metadata_uri_and_mime():
    resources = _run(mcp.list_resources())
    by_uri = {str(r.uri): r for r in resources}
    assert by_uri["config://runtime"].mimeType == "application/json"
    assert by_uri["catalog://products"].mimeType == "application/json"


def test_prompt_renders_question_and_guidance():
    res = _run(mcp.get_prompt("grounded_rag_prompt", {"question": "교환정책 알려줘"}))
    assert res.messages
    text = res.messages[0].content.text
    assert "교환정책" in text  # 인자가 실제로 렌더링됨
    assert "vector_search" in text  # 검색 먼저 지침 포함


# --- 무폴백 계약: 실제 도구 오류는 삼키지 말고 전파 + 세션은 닫힌다 ---------
def test_db_error_propagates_and_session_closed(monkeypatch):
    """DB 실패 시 도구가 오류를 전파하고(폴백 금지), with_db가 세션을 닫는지 확인."""

    class _FakeSession:
        def __init__(self):
            self.closed = False

        def query(self, *a, **k):
            raise RuntimeError("DB DOWN")

        def close(self):
            self.closed = True

    created: list[_FakeSession] = []

    def _factory():
        s = _FakeSession()
        created.append(s)
        return s

    monkeypatch.setattr(mcp_server, "SessionLocal", _factory)
    # get_price는 with_db → SessionLocal() → query()에서 예외 → 전파돼야 한다
    with pytest.raises(Exception, match="DB DOWN"):
        _run(mcp.call_tool("get_price", {"product_code": "P0001"}))
    # finally 블록이 세션을 닫았는가
    assert created and created[0].closed is True


def test_get_exchange_rate_never_opens_session(monkeypatch):
    """get_exchange_rate는 세션을 만들지 않는다 — SessionLocal 호출 시 실패시켜 증명."""

    def _boom():
        raise AssertionError("get_exchange_rate가 세션을 만들면 안 된다")

    monkeypatch.setattr(mcp_server, "SessionLocal", _boom)
    _blocks, structured = _run(mcp.call_tool("get_exchange_rate", {"currency": "USD"}))
    assert structured["ok"] is True
    assert structured["rate"] > 0
