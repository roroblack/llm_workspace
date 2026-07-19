"""LangChain 도구 래핑 테스트 (결정론적, 모델 없음)."""

import json

from app.agent.lc_tools import build_tools
from app.db.database import SessionLocal


def test_build_tools_count():
    db = SessionLocal()
    try:
        tools = build_tools(db)
        assert len(tools) == 6
        names = {t.name for t in tools}
        assert names == {
            "get_price",
            "get_stock",
            "get_order_status",
            "search_product",
            "get_exchange_rate",
            "search_knowledge_base",
        }
    finally:
        db.close()


def test_tool_invoke_matches_commerce_tools():
    db = SessionLocal()
    try:
        tools = {t.name: t for t in build_tools(db)}
        out = json.loads(tools["get_price"].invoke({"product_code": "P0001"}))
        assert out["ok"] is True
        assert out["price"] > 0

        fail = json.loads(tools["get_price"].invoke({"product_code": "NOPE"}))
        assert fail["ok"] is False
        assert fail["error_code"] == "product_not_found"
    finally:
        db.close()
