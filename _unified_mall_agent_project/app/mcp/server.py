"""MCP 서버 — 통합 기능을 MCP 표준 도구/리소스/프롬프트로 노출.

설계 원칙(RULE·계획 합의):
- 기존 `app.tools.commerce_tools` / `app.rag` / `app.ml` 함수를 **얇게 래핑**만 한다(중복 금지).
- 이 서버는 **별도 프로세스**로 stdio 전송된다(`python -m app.mcp.server`).
  FastAPI lifespan이 없으므로 **테이블 생성·seed를 하지 않는다.** DB가 준비돼 있지
  않으면 SQLAlchemy 예외가 그대로 MCP 오류로 전파된다(폴백·자동시딩 금지).
- DB가 필요한 도구는 `with_db`로 실행마다 세션 open/close. `get_exchange_rate`는
  DB를 쓰지 않으므로 세션을 만들지 않는다.
- 노출 도구는 **10개 고정**: 커머스5 + RAG2(vector_search/rag_qa) + ML3.
  `search_knowledge_base`는 `vector_search`와 중복이라 **제외**.

주의: "도구 실행마다 subprocess가 세션을 여는 구조"는 **학습용 시연**이며 운영 구조가
아니다(운영은 커넥션 풀·장수명 세션 등을 별도 설계).
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from typing import Any, TypeVar

# Windows 콘솔 stdio를 UTF-8로 (한글 도구 설명·인자 안전)
if sys.platform == "win32":  # pragma: no cover - 플랫폼 분기
    for _stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(_stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")

from mcp.server.fastmcp import FastMCP  # noqa: E402  (UTF-8 재설정 후 임포트)

from app.db.database import SessionLocal  # noqa: E402
from app.db.models import Product  # noqa: E402
from app.ml import intent as ml_intent  # noqa: E402
from app.ml import recommend as ml_recommend  # noqa: E402
from app.ml import sentiment as ml_sentiment  # noqa: E402
from app.rag import qa as rag_qa_mod  # noqa: E402
from app.rag import service as rag_service  # noqa: E402
from app.tools import commerce_tools  # noqa: E402

_T = TypeVar("_T")

mcp = FastMCP("seungmall")


def with_db(op: Callable[[Any], _T]) -> _T:
    """도구 실행마다 세션을 open/close 하고 결과를 반환한다.

    DB 미준비 등의 예외는 삼키지 않고 그대로 전파한다(폴백 금지).
    """
    db = SessionLocal()
    try:
        return op(db)
    finally:
        db.close()


# --------------------------------------------------------------------------
# 커머스 도구 5 (DB 필요 — get_exchange_rate만 예외)
# --------------------------------------------------------------------------
@mcp.tool()
def get_price(product_code: str) -> dict[str, Any]:
    """상품 코드로 판매가를 조회한다. 인자: product_code(예: 'P0001')."""
    return with_db(lambda db: commerce_tools.get_price(db, product_code))


@mcp.tool()
def get_stock(product_code: str) -> dict[str, Any]:
    """상품 코드로 재고 수량을 조회한다. 인자: product_code(예: 'P0001')."""
    return with_db(lambda db: commerce_tools.get_stock(db, product_code))


@mcp.tool()
def get_order_status(order_no: str) -> dict[str, Any]:
    """주문번호로 주문 상태를 조회한다. 인자: order_no."""
    return with_db(lambda db: commerce_tools.get_order_status(db, order_no))


@mcp.tool()
def search_product(keyword: str) -> dict[str, Any]:
    """상품명 키워드로 상품을 검색한다. 인자: keyword."""
    return with_db(lambda db: commerce_tools.search_product(db, keyword))


@mcp.tool()
def get_exchange_rate(currency: str) -> dict[str, Any]:
    """통화 코드의 원화 환율을 조회한다. 인자: currency('USD'/'EUR'/'JPY').

    환율표는 상수라 DB 세션을 만들지 않는다(계획 합의).
    """
    return commerce_tools.get_exchange_rate(None, currency)  # db 미사용


# --------------------------------------------------------------------------
# RAG 도구 2 (vector_search=검색, rag_qa=근거기반 답변)
# --------------------------------------------------------------------------
@mcp.tool()
def vector_search(query: str, top_k: int = 3, source: str | None = None) -> dict[str, Any]:
    """정책·매뉴얼 등 지식 문서를 벡터 검색한다. 인자: query, top_k, source(선택)."""
    results = rag_service.search(query, k=top_k, source=source)
    return {"ok": True, "count": len(results), "results": results}


@mcp.tool()
def rag_qa(question: str, top_k: int = 3) -> dict[str, Any]:
    """지식 문서 근거로 질문에 답한다(환각 억제·출처 인용). 인자: question, top_k.

    LLM 호출이 포함된다(설정된 provider 사용). 키/서버 없으면 예외 전파.
    """
    return rag_qa_mod.answer(question, k=top_k)


# --------------------------------------------------------------------------
# ML 도구 3 (감성/의도/추천)
# --------------------------------------------------------------------------
@mcp.tool()
def analyze_sentiment(text: str) -> dict[str, Any]:
    """리뷰/문의 텍스트의 감성(긍정/부정)을 분석한다(KoELECTRA). 인자: text."""
    return ml_sentiment.analyze_sentiment(text)


@mcp.tool()
def classify_intent(text: str) -> dict[str, Any]:
    """고객 문의의 의도를 규칙 기반으로 분류한다. 인자: text."""
    return ml_intent.classify_intent(text)


@mcp.tool()
def recommend_products(query: str, top_k: int = 3) -> dict[str, Any]:
    """질의와 임베딩 유사도로 상품을 추천한다. 인자: query, top_k."""
    return with_db(lambda db: ml_recommend.recommend_products(db, query, top_k=top_k))


# --------------------------------------------------------------------------
# 리소스 2
# --------------------------------------------------------------------------
@mcp.resource("config://runtime", mime_type="application/json")
def runtime_config() -> str:
    """런타임 설정(비밀 제외)을 JSON으로 노출한다."""
    from app.core.config import get_settings

    s = get_settings()
    payload = {
        "llm_provider": s.LLM_PROVIDER,
        "local_model": s.LOCAL_MODEL,
        "openai_model": s.OPENAI_MODEL,
        "gemini_model": s.GEMINI_MODEL,
        "embedding_model": s.ST_EMBEDDING_MODEL,
        "rag_top_k": s.RAG_TOP_K,
        "sentiment_model": s.SENTIMENT_MODEL,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


@mcp.resource("catalog://products", mime_type="application/json")
def product_catalog() -> str:
    """상품 카탈로그를 JSON으로 노출한다(자체 세션 open/close)."""

    def _load(db: Any) -> list[dict[str, Any]]:
        rows = db.query(Product).order_by(Product.product_code).all()
        return [
            {
                "product_code": p.product_code,
                "name": p.name,
                "category": p.category,
                "price": p.price,
            }
            for p in rows
        ]

    items = with_db(_load)
    return json.dumps({"count": len(items), "products": items}, ensure_ascii=False, indent=2)


# --------------------------------------------------------------------------
# 프롬프트 1
# --------------------------------------------------------------------------
@mcp.prompt()
def grounded_rag_prompt(question: str) -> str:
    """검색 먼저·근거만 사용하는 RAG 지침 프롬프트를 생성한다."""
    return (
        "너는 승승장구몰 고객지원 AI다. 반드시 아래 절차를 지켜라.\n"
        "1) 먼저 vector_search 도구로 관련 근거를 검색한다.\n"
        "2) 검색된 근거에 있는 내용만 사용해 답한다(모르면 모른다고 답한다).\n"
        "3) 답변 끝에 사용한 출처를 명시한다.\n\n"
        f"질문: {question}"
    )


if __name__ == "__main__":  # pragma: no cover - stdio 진입점
    mcp.run(transport="stdio")
