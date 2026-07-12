"""커머스 도구를 LangChain @tool로 래핑 (Phase 3.5).

commerce_tools의 순수 함수를 재사용하고, db 세션을 클로저로 바인딩한다(전역 세션
금지). 반환은 LangChain 관례에 따라 JSON 문자열로 통일한다.
"""

from __future__ import annotations

import json

from langchain_core.tools import BaseTool, tool
from sqlalchemy.orm import Session

from app.tools import commerce_tools as C


def _dumps(obj: dict) -> str:
    return json.dumps(obj, ensure_ascii=False)


def build_tools(db: Session) -> list[BaseTool]:
    """db에 바인딩된 LangChain 도구 5종을 반환한다."""

    @tool
    def get_price(product_code: str) -> str:
        """상품 코드로 가격을 조회한다. 인자: product_code (예: 'P0001')."""
        return _dumps(C.get_price(db, product_code))

    @tool
    def get_stock(product_code: str) -> str:
        """상품 코드로 재고와 재주문 필요 여부를 조회한다. 인자: product_code."""
        return _dumps(C.get_stock(db, product_code))

    @tool
    def get_order_status(order_no: str) -> str:
        """주문번호로 주문 상태와 금액을 조회한다. 인자: order_no."""
        return _dumps(C.get_order_status(db, order_no))

    @tool
    def search_product(keyword: str) -> str:
        """상품명 키워드로 상품 목록을 검색한다. 인자: keyword."""
        return _dumps(C.search_product(db, keyword))

    @tool
    def get_exchange_rate(currency: str) -> str:
        """통화 코드(USD/EUR/JPY)의 원화 환율을 조회한다. 인자: currency."""
        return _dumps(C.get_exchange_rate(db, currency))

    @tool
    def search_knowledge_base(query: str) -> str:
        """정책·매뉴얼 등 지식 문서를 검색한다(RAG). 인자: query(자연어 질문)."""
        return _dumps(C.search_knowledge_base(db, query))

    return [
        get_price,
        get_stock,
        get_order_status,
        search_product,
        get_exchange_rate,
        search_knowledge_base,
    ]
