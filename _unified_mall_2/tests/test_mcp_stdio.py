"""MCP stdio 왕복 스모크 — 실제 서브프로세스 서버를 stdio로 기동해 통신.

`@pytest.mark.mcp`: 서브프로세스(파이썬 재기동) 비용이 있어 기본 CI에서 제외한다
(CI = "not llm and not ml and not mcp"). LLM/모델이 필요한 도구(rag_qa/analyze_sentiment/
recommend_products)는 여기서 호출하지 않는다 — 결정론적 비-LLM 도구만 왕복 검증한다.

서브프로세스 서버는 conftest가 만든 임시 DB(DATABASE_URL 환경변수)를 클라이언트가
env로 물려주므로 동일 파일을 본다. 서버는 스스로 테이블 생성/seed 하지 않는다(계획 합의).
"""

from __future__ import annotations

import asyncio

import pytest

from app.core.errors import ValidationErr
from app.mcp import client as mcp_client
from tests.test_mcp import EXPECTED_TOOLS  # 도구 이름 집합 단일 출처(중복 방지)

pytestmark = pytest.mark.mcp


def _run(coro):
    return asyncio.run(coro)


def test_stdio_list_tools_exact_set():
    tools = _run(mcp_client.list_tools())
    names = {t["name"] for t in tools}
    # 정확한 이름 집합 비교 — 잘못된 도구가 섞이면 실패해야 한다
    assert names == EXPECTED_TOOLS
    # 각 도구가 입력 스키마를 노출하는지(계약)
    by_name = {t["name"]: t for t in tools}
    assert "product_code" in by_name["get_price"]["input_schema"]["properties"]
    assert "currency" in by_name["get_exchange_rate"]["input_schema"]["properties"]


def test_stdio_call_get_price():
    result = _run(mcp_client.call_tool("get_price", {"product_code": "P0001"}))
    assert result["structured"]["ok"] is True
    assert result["structured"]["price"] > 0


def test_stdio_call_get_exchange_rate():
    result = _run(mcp_client.call_tool("get_exchange_rate", {"currency": "USD"}))
    assert result["structured"]["rate"] > 0


def test_stdio_business_failure_is_not_error():
    # 없는 상품 = 비즈니스 실패 → isError 아님(구조화 ok:False), 예외로 승격되지 않는다
    result = _run(mcp_client.call_tool("get_price", {"product_code": "NOPE"}))
    assert result["structured"]["ok"] is False
    assert result["structured"]["error_code"] == "product_not_found"


def test_stdio_unknown_tool_raises_validation_error():
    # 알 수 없는 도구 = 사용자 입력 오류 → 200 성공으로 감추지 않고 ValidationErr(422)로 전파
    with pytest.raises(ValidationErr):
        _run(mcp_client.call_tool("nonexistent_tool", {}))


def test_stdio_missing_required_arg_raises_validation_error():
    # 필수 인자 누락 = 인자 검증 실패 → ValidationErr(422)
    with pytest.raises(ValidationErr):
        _run(mcp_client.call_tool("get_price", {}))


def test_stdio_top_k_out_of_range_raises_validation_error():
    # top_k 범위 밖(0) → 스키마 검증 실패 → ValidationErr(422). 조용히 기본값 폴백 아님.
    with pytest.raises(ValidationErr):
        _run(mcp_client.call_tool("vector_search", {"query": "환불", "top_k": 0}))


def test_stdio_tool_internal_validation_error_maps_422():
    # 도구 내부에서 낸 ValidationErr(빈 질문)이 프로토콜 경계를 넘어도 503이 아닌
    # 422로 복원돼야 한다(서버가 error_code를 실어 보내고 클라이언트가 복원).
    with pytest.raises(ValidationErr):
        _run(mcp_client.call_tool("rag_qa", {"question": "   "}))
