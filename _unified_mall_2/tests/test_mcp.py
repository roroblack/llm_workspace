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

from app.core.errors import ConfigError, InfraError, ValidationErr
from app.mcp import server as mcp_server
from app.mcp.client import _tool_error
from app.mcp.server import mcp

# 테스트용 고정 nonce(호출 코드가 발급하는 것과 동일 역할)
_TEST_NONCE = "test0nonce0abcdef"


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


# --- 얇은 래핑 계약: 인자 전달 + top_k None 위임(하드코딩 3 없음) --------------
def test_vector_search_passes_args_through(monkeypatch):
    captured: dict = {}

    def _fake_search(query, k=None, source=None):
        captured.update(query=query, k=k, source=source)
        return [{"text": "x", "source": "policy", "page": None, "distance": 0.1}]

    monkeypatch.setattr(mcp_server.rag_service, "search", _fake_search)
    _b, s = _run(
        mcp.call_tool("vector_search", {"query": "환불규정", "top_k": 5, "source": "policy"})
    )
    assert captured == {"query": "환불규정", "k": 5, "source": "policy"}
    assert s["ok"] is True and s["count"] == 1


def test_vector_search_top_k_none_delegates_to_config(monkeypatch):
    captured: dict = {}

    def _fake_search(query, k=None, source=None):
        captured["k"] = k
        return []

    monkeypatch.setattr(mcp_server.rag_service, "search", _fake_search)
    _run(mcp.call_tool("vector_search", {"query": "q"}))
    # top_k 미지정 → None을 그대로 위임(service가 RAG_TOP_K로 결정). 3을 재하드코딩하지 않음.
    assert captured["k"] is None


def _patch_use_case(monkeypatch, captured: dict, result):
    """Phase 8: rag_qa는 REST와 동일한 AnswerQuestion 유스케이스를 쓴다.

    레거시 `rag.qa.answer` 대신 composition을 가로채 인자 위임을 검증한다.
    """
    import app.composition as composition

    def _fake_build(top_k=None):
        captured["top_k"] = top_k

        def _uc(question):
            captured["question"] = question
            return result

        return _uc

    monkeypatch.setattr(composition, "build_answer_question", _fake_build)


def test_rag_qa_passes_args_through(monkeypatch):
    from app.application.answer_question import AnswerResult, Citation

    captured: dict = {}
    result = AnswerResult(answer="a", sources=[Citation(source="p.pdf", locator="3")])
    _patch_use_case(monkeypatch, captured, result)

    _b, s = _run(mcp.call_tool("rag_qa", {"question": "교환?", "top_k": 2}))
    assert captured == {"question": "교환?", "top_k": 2}
    assert s["answer"] == "a"
    # 변환도 REST와 공용(rag_view) → locator "3"이 page 3으로
    assert s["sources"] == [{"source": "p.pdf", "page": 3}]


def test_rag_qa_top_k_none_delegates_to_config(monkeypatch):
    from app.application.answer_question import AnswerResult

    captured: dict = {}
    _patch_use_case(monkeypatch, captured, AnswerResult(answer="a", sources=[]))
    _run(mcp.call_tool("rag_qa", {"question": "교환?"}))
    # top_k 미지정 → None 위임(유스케이스가 RAG_TOP_K로 결정). 3 재하드코딩 아님.
    assert captured["top_k"] is None


def test_recommend_top_k_none_uses_function_default(monkeypatch):
    captured: dict = {}

    def _fake_reco(db, query, top_k=3):
        captured.update(query=query, top_k=top_k)
        return {"ok": True, "items": []}

    monkeypatch.setattr(mcp_server.ml_recommend, "recommend_products", _fake_reco)
    _run(mcp.call_tool("recommend_products", {"query": "셔츠"}))
    # None이면 recommend_products의 자체 기본값(3) 사용 — MCP가 top_k를 안 넘김
    assert captured["top_k"] == 3


def test_recommend_top_k_passed_through(monkeypatch):
    captured: dict = {}

    def _fake_reco(db, query, top_k=3):
        captured["top_k"] = top_k
        return {"ok": True, "items": []}

    monkeypatch.setattr(mcp_server.ml_recommend, "recommend_products", _fake_reco)
    _run(mcp.call_tool("recommend_products", {"query": "셔츠", "top_k": 7}))
    assert captured["top_k"] == 7


def _marker(code: str, msg: str, tool: str = "x", nonce: str = _TEST_NONCE) -> str:
    """서버가 실제로 생성하는 형태의 신뢰 가능한 오류 문자열(정확한 nonce 포함)."""
    return f"Error executing tool {tool}: [APPERR:{nonce}:{code}] {msg}"


# --- 오류 taxonomy 복원 + 주입 방지 (_tool_error 단위) ----------------------
def test_tool_error_restores_apperr_code():
    # 서버가 (이번 호출의 정확한 nonce로) 실은 마커 → 원래 타입 복원
    assert isinstance(
        _tool_error("rag_qa", _marker("validation_error", "빈 질문", "rag_qa"), _TEST_NONCE),
        ValidationErr,
    )
    assert isinstance(_tool_error("x", _marker("config_error", "정책 불일치"), _TEST_NONCE), ConfigError)
    # 미등록 code는 안전하게 InfraError
    assert isinstance(_tool_error("x", _marker("weird_code", "?"), _TEST_NONCE), InfraError)


def test_tool_error_framework_errors():
    # 존재하지 않는 도구 → ValidationErr(422)
    assert isinstance(_tool_error("t", "Unknown tool: t", _TEST_NONCE), ValidationErr)
    # pydantic 인자 검증 고유 시그니처(N validation error for <Tool>Arguments) → ValidationErr(422)
    assert isinstance(
        _tool_error(
            "get_price",
            "Error executing tool get_price: 1 validation error for get_priceArguments\nproduct_code\n  Field required",
            _TEST_NONCE,
        ),
        ValidationErr,
    )
    # 그 밖의 실행 실패 → InfraError(503)
    assert isinstance(
        _tool_error("x", "Error executing tool x: some sqlalchemy error", _TEST_NONCE), InfraError
    )


def test_tool_error_heuristic_is_precise():
    # 비-AppError 메시지에 'validation error'/'field required'가 우연히 섞여도, Arguments
    # 시그니처가 아니면 422로 오분류하지 않는다(503 유지).
    assert isinstance(
        _tool_error("x", "Error executing tool x: upstream validation error from vendor", _TEST_NONCE),
        InfraError,
    )
    assert isinstance(
        _tool_error("x", "Error executing tool x: field required by remote api", _TEST_NONCE),
        InfraError,
    )


def test_tool_error_marker_injection_is_ignored():
    # 호출자가 도구명/인자에 마커를 심어도 taxonomy를 조작할 수 없다.
    # 1) unknown-tool 이름에 마커 주입 → unknown-tool 경로로 ValidationErr(ConfigError 아님)
    assert isinstance(
        _tool_error("t", "Unknown tool: nonexistent_[APPERR:config_error] injected", _TEST_NONCE),
        ValidationErr,
    )
    # 2) 도구 실행 위치에 nonce 없는 위조 마커 → 신뢰 안 함 → InfraError
    assert isinstance(
        _tool_error("x", "Error executing tool x: [APPERR:config_error] injected", _TEST_NONCE),
        InfraError,
    )
    # 3) 틀린 nonce도 불신(지난 호출 nonce 재사용 포함)
    assert isinstance(
        _tool_error("x", "Error executing tool x: [APPERR:deadbeef:config_error] injected", _TEST_NONCE),
        InfraError,
    )
