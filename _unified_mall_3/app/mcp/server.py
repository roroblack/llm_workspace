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
import os
import sys
from collections.abc import Callable
from typing import Annotated, Any, TypeVar

from pydantic import Field

# Windows 콘솔 stdio를 UTF-8로 (한글 도구 설명·인자 안전)
if sys.platform == "win32":  # pragma: no cover - 플랫폼 분기
    for _stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(_stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")

from mcp.server.fastmcp import FastMCP  # noqa: E402  (UTF-8 재설정 후 임포트)

from app.core.config import get_settings  # noqa: E402
from app.core.errors import AppError  # noqa: E402
from app.db.database import SessionLocal  # noqa: E402
from app.ml import intent as ml_intent  # noqa: E402
from app.ml import recommend as ml_recommend  # noqa: E402
from app.ml import sentiment as ml_sentiment  # noqa: E402
from app.rag import service as rag_service  # noqa: E402
from app.tools import commerce_tools  # noqa: E402

_T = TypeVar("_T")

# top_k는 스키마 수준에서 1~10 범위 검증(범위 밖=인자 검증 오류). None이면 각 함수의
# 기본값(RAG_TOP_K 등 config)으로 위임 — 매직값 3을 여기서 중복 하드코딩하지 않는다.
TopK = Annotated[int, Field(ge=1, le=10)]

# MCP 서버 이름은 브랜드 변수를 따른다(하드코딩·구 브랜드 잔재 금지 — 하나만 바꾸면 전파).
mcp = FastMCP(get_settings().BRAND_NAME)


# 클라이언트가 서브프로세스를 띄우며 넘겨준 1회용 nonce. 이게 있어야만 마커를 신뢰받는다.
# (없으면=외부 클라이언트 직접 실행 → 마커를 실지 않는다. 위조 불가: 호출자 입력이 nonce를
#  재현할 수 없으므로 인자에 마커를 심어도 taxonomy를 조작하지 못한다.)
_APPERR_NONCE = os.environ.get("MCP_APPERR_NONCE")


def _encode_apperr(exc: AppError) -> BaseException:
    """도구 내부 AppError의 error_code를 프로토콜 경계 너머로 보존한다.

    FastMCP가 예외를 문자열화하면 타입이 사라진다. 클라이언트가 원래 타입(422/503 등)을
    복원할 수 있도록 '[APPERR:<nonce>:<code>]' 마커를 실어 재발생시킨다. nonce는 클라이언트가
    넘긴 비밀값이라 호출자 입력으로 위조할 수 없다(주입 방지). nonce가 없으면 원본을 그대로
    전파한다(외부 클라이언트는 우리 taxonomy 복원을 쓰지 않음).
    """
    if _APPERR_NONCE:
        return RuntimeError(f"[APPERR:{_APPERR_NONCE}:{exc.error_code}] {exc.message}")
    return exc


def with_db(op: Callable[[Any], _T]) -> _T:
    """도구 실행마다 세션을 open/close 하고 결과를 반환한다.

    DB 미준비 등의 예외는 삼키지 않고 전파한다(폴백 금지). 도구가 낸 AppError는
    error_code를 보존해 재발생시킨다.
    """
    db = SessionLocal()
    try:
        return op(db)
    except AppError as exc:
        raise _encode_apperr(exc) from exc
    finally:
        db.close()


def _guard(op: Callable[[], _T]) -> _T:
    """세션이 필요 없는 도구용 — AppError의 error_code를 보존해 재발생시킨다."""
    try:
        return op()
    except AppError as exc:
        raise _encode_apperr(exc) from exc


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
    return _guard(lambda: commerce_tools.get_exchange_rate(None, currency))  # db 미사용


# --------------------------------------------------------------------------
# RAG 도구 2 (vector_search=검색, rag_qa=근거기반 답변)
# --------------------------------------------------------------------------
@mcp.tool()
def vector_search(
    query: str, top_k: TopK | None = None, source: str | None = None
) -> dict[str, Any]:
    """정책·매뉴얼 등 지식 문서를 벡터 검색한다. 인자: query, top_k(1~10, 미지정=기본), source(선택)."""

    def _run() -> dict[str, Any]:
        results = rag_service.search(query, k=top_k, source=source)  # None→RAG_TOP_K
        return {"ok": True, "count": len(results), "results": results}

    return _guard(_run)


@mcp.tool()
def rag_qa(question: str, top_k: TopK | None = None) -> dict[str, Any]:
    """지식 문서 근거로 질문에 답한다(환각 억제·출처 인용). 인자: question, top_k(1~10, 미지정=기본).

    LLM 호출이 포함된다(설정된 provider 사용). 키/서버 없으면 예외 전파.

    Phase 8 parity: REST `/api/rag/qa`와 **동일한 AnswerQuestion 유스케이스 + 동일한 변환**
    (`rag_view.answer_to_dict`)을 쓴다. 구현이 두 벌이 되지 않도록 레거시 `rag.qa`는 제거됐다.
    """

    def _run() -> dict[str, Any]:
        from app.adapters.rag_view import answer_to_dict
        from app.composition import build_answer_question

        return answer_to_dict(build_answer_question(top_k=top_k)(question))  # None→RAG_TOP_K

    return _guard(_run)


# --------------------------------------------------------------------------
# ML 도구 3 (감성/의도/추천)
# --------------------------------------------------------------------------
@mcp.tool()
def analyze_sentiment(text: str) -> dict[str, Any]:
    """리뷰/문의 텍스트의 감성(긍정/부정)을 분석한다(KoELECTRA). 인자: text."""
    return _guard(lambda: ml_sentiment.analyze_sentiment(text))


@mcp.tool()
def classify_intent(text: str) -> dict[str, Any]:
    """고객 문의의 의도를 규칙 기반으로 분류한다. 인자: text."""
    return _guard(lambda: ml_intent.classify_intent(text))


@mcp.tool()
def recommend_products(query: str, top_k: TopK | None = None) -> dict[str, Any]:
    """질의와 임베딩 유사도로 상품을 추천한다. 인자: query, top_k(1~10, 미지정=기본)."""
    # None이면 recommend_products의 자체 기본값에 위임(여기서 3을 재하드코딩하지 않음).
    kwargs = {} if top_k is None else {"top_k": top_k}
    return with_db(lambda db: ml_recommend.recommend_products(db, query, **kwargs))


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
        from app.services.catalog_query import list_products

        # 질의는 REST와 공용 1벌(세션 독립 DTO 반환), 세션 수명은 with_db가 소유.
        # projection은 의도적으로 REST와 다르다 — 이 리소스 계약은 재고를 노출하지 않는다.
        return [
            {
                "product_code": p.product_code,
                "name": p.name,
                "category": p.category,
                "price": p.price,
            }
            for p in list_products(db)
        ]

    items = with_db(_load)
    return json.dumps({"count": len(items), "products": items}, ensure_ascii=False, indent=2)


# --------------------------------------------------------------------------
# 프롬프트 1
# --------------------------------------------------------------------------
@mcp.prompt()
def grounded_rag_prompt(question: str) -> str:
    """검색 먼저·근거만 사용하는 RAG 지침 프롬프트를 생성한다."""
    from app.core.config import get_settings

    return (
        f"너는 {get_settings().BRAND_NAME} 고객지원 AI다. 반드시 아래 절차를 지켜라.\n"
        "1) 먼저 vector_search 도구로 관련 근거를 검색한다.\n"
        "2) 검색된 근거에 있는 내용만 사용해 답한다(모르면 모른다고 답한다).\n"
        "3) 답변 끝에 사용한 출처를 명시한다.\n\n"
        f"질문: {question}"
    )


def _warm_up_rag_store() -> None:
    """임베딩·FAISS 인덱스를 stdio 서버 루프 시작 **전에** 미리 로드한다.

    **이것은 우회책(workaround)이지 근본 수정이 아니다** — SDK 내부의 정확한 원인(어느
    메커니즘이 지연 로딩과 stdio 루프를 충돌시키는지)은 특정하지 못했다(Codex 지적,
    Phase 10 후속 조사 리포트 참조). 재현으로 검증한 사실만 안다: mcp.run(transport=
    "stdio")의 stdio 루프가 이미 돌고 있는 동안 vector_search 도구 안에서 임베딩을
    **지연** 로드하면 180초+ 응답이 없었고, 같은 로딩을 mcp.run() 시작 **전**에 하면
    22~27초로 매번 정상 완료됐다.

    **트레이드오프(정직하게 기록)**: MCP는 호출마다 새 subprocess를 띄우므로, 이 워밍업은
    vector_search/rag_qa/recommend_products와 무관한 `get_price` 같은 가벼운 도구 호출도
    똑같이 부담한다(서브프로세스 1회 기동당 ~25초 고정비). 실측: stdio 통합 테스트
    스위트가 17초 → 245초로 느려졌다(전부 통과는 함). 인덱스 로드가 실패하면(예: 파일
    없음) **RAG와 무관한 다른 9개 도구까지 서버가 아예 못 뜬다**는 것도 인지된 위험이다.
    범위를 **재현이 확인된 것(임베딩·FAISS)만**으로 좁혔다 — 감성분석 모델은 같은
    문제가 있는지 검증한 적이 없어 추측만으로 워밍업에 넣지 않는다(Codex 지적 반영).

    이 함수는 stdio 진입점(`__main__`)에서만 호출된다 — 테스트가 이 모듈을 인프로세스로
    import할 때(`test_mcp.py`)는 실행되지 않아 결정론 테스트에 무거운 모델 로드를 강요하지 않는다.
    """
    from app.rag import service as rag_service

    rag_service.get_store()


if __name__ == "__main__":  # pragma: no cover - stdio 진입점
    _warm_up_rag_store()
    mcp.run(transport="stdio")
