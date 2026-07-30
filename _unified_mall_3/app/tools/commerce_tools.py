"""커머스 도구 (DB 기반).

좋은 도구 5원칙(PDF6): 한 가지 일 / 이름=기능 / 명확한 인자 / 구체적 독스트링 /
일관된 반환. 각 도구는 dict를 반환한다.

오류 처리 원칙 (Codex 합의):
- 예상된 '비즈니스 실패'(없는 상품/주문 등)는 {"ok": false, "error_code", "message"}로
  구조화 관찰을 반환한다 (에이전트가 멈추지 않도록).
- 인프라 실패(DB 다운 등 예상 밖 예외)는 삼키지 않고 그대로 전파한다.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.db.models import Inventory, Order, Product

# 고정 환율표 (외부 호출 없음). config 상수로 이름 붙여 선언 (하드코딩 매직넘버 아님)
EXCHANGE_RATES: dict[str, float] = {"USD": 1350.0, "EUR": 1450.0, "JPY": 9.0}


def _fail(code: str, message: str) -> dict[str, Any]:
    return {"ok": False, "error_code": code, "message": message}


def get_price(db: Session, product_code: str) -> dict[str, Any]:
    """상품 코드로 가격을 조회한다. 인자: product_code(예: 'P0001')."""
    product = db.query(Product).filter(Product.product_code == product_code).first()
    if product is None:
        return _fail("product_not_found", f"상품을 찾을 수 없습니다: {product_code}")
    return {"ok": True, "product_name": product.name, "price": product.price}


def get_stock(db: Session, product_code: str) -> dict[str, Any]:
    """상품 코드로 재고와 재주문 필요 여부를 조회한다. 인자: product_code."""
    product = db.query(Product).filter(Product.product_code == product_code).first()
    if product is None:
        return _fail("product_not_found", f"상품을 찾을 수 없습니다: {product_code}")
    inv = db.query(Inventory).filter(Inventory.product_id == product.id).first()
    stock = inv.stock if inv else 0
    reorder = inv.reorder_level if inv else 0
    return {
        "ok": True,
        "product_name": product.name,
        "stock": stock,
        "reorder_level": reorder,
        "need_reorder": stock <= reorder,
    }


def get_order_status(db: Session, order_no: str) -> dict[str, Any]:
    """주문번호로 주문 상태와 금액을 조회한다. 인자: order_no(예: 'O123...')."""
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if order is None:
        return _fail("order_not_found", f"주문을 찾을 수 없습니다: {order_no}")
    return {
        "ok": True,
        "order_no": order.order_no,
        "status": order.status,
        "total_amount": order.total_amount,
    }


def search_product(db: Session, keyword: str) -> dict[str, Any]:
    """상품명 키워드로 상품 목록을 검색한다. 인자: keyword(부분 일치)."""
    rows = db.query(Product).filter(Product.name.contains(keyword)).all()
    results = [{"code": p.product_code, "name": p.name, "price": p.price} for p in rows]
    return {"ok": True, "count": len(results), "results": results}


def get_exchange_rate(db: Session | None, currency: str) -> dict[str, Any]:
    """통화 코드의 원화 환율을 조회한다. 인자: currency('USD'/'EUR'/'JPY').

    환율표는 상수라 db를 사용하지 않는다. 도구 시그니처 일관성(TOOL_MAP의
    `fn(db, **args)` 디스패치)을 위해 db 인자는 유지하되 타입을 `Session | None`으로
    두어 세션 없이도 호출 가능함을 정적으로 명시한다(MCP 서버가 None을 넘김).
    """
    rate = EXCHANGE_RATES.get(currency.upper())
    if rate is None:
        return _fail("currency_not_supported", f"지원하지 않는 통화입니다: {currency}")
    return {"ok": True, "currency": currency.upper(), "rate": rate}


def search_knowledge_base(db: Session, query: str) -> dict[str, Any]:
    """정책·매뉴얼 등 지식 문서를 검색한다(RAG). 인자: query(자연어 질문)."""
    # db 인자는 도구 시그니처 일관성용(RAG는 벡터스토어 사용).
    from app.rag.service import search

    results = search(query)
    return {"ok": True, "count": len(results), "results": results}


def preview_order(db: Session, items_json: str) -> dict[str, Any]:
    """주문을 **미리보기**한다(주문을 생성하지 않음). 인자: items_json
    (예: '[{"product_code":"P0001","quantity":2}]'). 총액·재고 충족 여부를 계산해 돌려준다."""
    import json

    from app.application.commerce import OrderLine
    from app.composition import build_preview_order

    try:
        raw = json.loads(items_json)
        lines = [
            OrderLine(product_code=str(it["product_code"]), quantity=int(it["quantity"]))
            for it in raw
        ]
    except (ValueError, TypeError, KeyError) as exc:
        # 인자 형식 오류는 예상된 '비즈니스 실패' → 관찰로 돌려 에이전트가 고쳐 부르게 한다.
        return _fail("bad_arguments", f"items_json 형식 오류: {exc}")

    try:
        preview = build_preview_order(db)(lines)
    except Exception as exc:  # noqa: BLE001 — 검증 실패(빈 목록·수량<=0)를 관찰로 전달
        from app.core.errors import ValidationErr

        if isinstance(exc, ValidationErr):
            return _fail("invalid_items", str(exc))
        raise  # 인프라 실패는 삼키지 않고 전파
    return {
        "ok": True,
        "total": preview.total,
        "feasible": preview.feasible,
        "issues": preview.issues,
        "lines": [
            {
                "product_code": ln.product_code,
                "name": ln.name,
                "unit_price": ln.unit_price,
                "quantity": ln.quantity,
                "subtotal": ln.subtotal,
                "available": ln.available,
                "sufficient": ln.sufficient,
            }
            for ln in preview.lines
        ],
        # 이 응답은 승인 토큰이 아니다 — 가격·재고는 변할 수 있고 주문은 사용자의 명시 승인으로만 성립.
        "note": "미리보기입니다. 주문은 생성되지 않았습니다. 가격·재고는 변동될 수 있으며, "
        "실제 주문은 사용자가 Idempotency-Key와 함께 승인해야 성립합니다.",
    }


# name → callable (db, **args). **읽기 전용만** 등록한다(쓰기 도구 금지 — TEST-AGT-NOWRITE-001).
TOOL_MAP = {
    "get_price": get_price,
    "get_stock": get_stock,
    "get_order_status": get_order_status,
    "search_product": search_product,
    "get_exchange_rate": get_exchange_rate,
    "search_knowledge_base": search_knowledge_base,
    "preview_order": preview_order,
}


def _schema(name: str, desc: str, prop: str, prop_desc: str) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": desc,
            "parameters": {
                "type": "object",
                "properties": {prop: {"type": "string", "description": prop_desc}},
                "required": [prop],
            },
        },
    }


# OpenAI function-calling 스키마
TOOLS_SCHEMA = [
    _schema("get_price", "상품 코드로 가격 조회", "product_code", "상품 코드 예: P0001"),
    _schema("get_stock", "상품 코드로 재고/재주문 필요 조회", "product_code", "상품 코드"),
    _schema("get_order_status", "주문번호로 상태/금액 조회", "order_no", "주문번호"),
    _schema("search_product", "상품명 키워드 검색", "keyword", "검색 키워드"),
    _schema("get_exchange_rate", "통화 환율 조회", "currency", "USD/EUR/JPY"),
    _schema("search_knowledge_base", "정책·매뉴얼 지식 문서 검색(RAG)", "query", "자연어 질문"),
    _schema(
        "preview_order",
        "주문 미리보기(주문을 생성하지 않음). 총액·재고 충족 여부 계산",
        "items_json",
        '주문 항목 JSON 배열 예: [{"product_code":"P0001","quantity":2}]',
    ),
]
