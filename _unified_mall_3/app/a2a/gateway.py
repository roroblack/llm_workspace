"""A2A 위임 게이트웨이 — 대상 전문 에이전트로 작업을 라우팅한다.

각 전문 에이전트는 **기존 서비스를 얇게 재사용**한다(commerce_tools / rag / recommend).
무폴백: 미등록 에이전트·빈 입력·필수 식별자 누락은 문자열로 얼버무리지 않고 ValidationErr로
명시적으로 실패한다. 비즈니스 실패(없는 주문/상품)는 각 서비스의 구조화 관찰({ok:false,...})을
그대로 반환한다 — 이는 폴백이 아니라 정의된 관찰 결과다.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from sqlalchemy.orm import Session

from app.a2a.cards import AGENT_CARDS
from app.core.errors import ValidationErr
from app.tools import commerce_tools

# 주문번호(O + 6자리)·상품코드(P + 4자리) — 실데이터 형식(data/orders.csv, products.csv).
_ORDER_RE = re.compile(r"\bO\d{6}\b", re.IGNORECASE)
_PRODUCT_RE = re.compile(r"\bP\d{4}\b", re.IGNORECASE)


def _find(pattern: re.Pattern[str], message: str) -> str:
    m = pattern.search(message)
    return m.group(0).upper() if m else ""


def _order_agent(db: Session, message: str) -> dict[str, object]:
    order_no = _find(_ORDER_RE, message)
    if not order_no:
        raise ValidationErr("주문번호를 O000000 형식으로 입력해 주세요.")
    return commerce_tools.get_order_status(db, order_no)


def _catalog_agent(db: Session, message: str) -> dict[str, object]:
    code = _find(_PRODUCT_RE, message)
    if code:
        # 카드가 광고한 두 능력(재고 조회·가격 조회)을 메시지 의도로 분기 — 카드-실행 계약 일치.
        if any(kw in message for kw in ("가격", "얼마", "price")):
            return commerce_tools.get_price(db, code)
        return commerce_tools.get_stock(db, code)
    keyword = message.strip()
    if not keyword:
        raise ValidationErr("상품명 또는 상품코드(P0001 형식)를 입력해 주세요.")
    return commerce_tools.search_product(db, keyword)


def _knowledge_agent(db: Session, message: str) -> dict[str, object]:
    query = message.strip()
    if not query:
        raise ValidationErr("검색할 질문을 입력해 주세요.")
    # 정책/FAQ 지식 검색 — 기존 커머스 도구 그대로 재사용(중복 구현 금지).
    return commerce_tools.search_knowledge_base(db, query)


def _recommend_agent(db: Session, message: str) -> dict[str, object]:
    query = message.strip()
    if not query:
        raise ValidationErr("추천을 위한 질의를 입력해 주세요.")
    from app.ml import recommend as ml_recommend

    return ml_recommend.recommend_products(db, query)


# 에이전트 이름 → 핸들러(db, message).
_HANDLERS: dict[str, Callable[[Session, str], dict[str, object]]] = {
    "order-agent": _order_agent,
    "catalog-agent": _catalog_agent,
    "knowledge-agent": _knowledge_agent,
    "recommend-agent": _recommend_agent,
}

# 카드(cards.py)와 핸들러(여기) 이중 레지스트리가 조용히 어긋나는 걸 **import 시점에 fail-fast**로
# 막는다 — 카드만 추가하고 핸들러를 빠뜨리면 호출 시 KeyError가 아니라 여기서 즉시 실패(무폴백).
_DRIFT = set(AGENT_CARDS) ^ set(_HANDLERS)
if _DRIFT:
    raise RuntimeError(f"A2A 카드/핸들러 레지스트리 불일치: {sorted(_DRIFT)}")


def delegate_to_agent(db: Session, target_agent: str, message: str) -> dict[str, object]:
    """대상 전문 에이전트에 작업을 위임한다. 미등록/빈 입력은 ValidationErr(무폴백)."""
    if target_agent not in AGENT_CARDS:
        raise ValidationErr(f"등록되지 않은 A2A 에이전트입니다: {target_agent}")
    if not message or not message.strip():
        raise ValidationErr("메시지가 비어 있습니다.")
    return _HANDLERS[target_agent](db, message)
