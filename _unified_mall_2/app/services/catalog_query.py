"""카탈로그 조회 공용 질의(Phase 8) — REST 라우터와 MCP 리소스가 같은 질의를 쓴다.

**세션 수명은 호출자가 소유한다**(여기서 열지도 닫지도 커밋하지도 않는다). REST는 요청 스코프
세션을, MCP는 자체 open/close 세션을 각각 소유하므로, 공용 함수가 세션을 관리하면 경계가 깨진다.

**ORM 객체가 아니라 불변 DTO를 반환한다**(Codex 지적): ORM 행을 넘기면 세션이 닫힌 뒤
지연 로딩 속성 접근에서 `DetachedInstanceError`가 날 수 있다. 관계(inventory)까지 **세션 안에서**
즉시 해석해 DTO로 굳혀 내보내면 호출자는 세션 수명과 무관하게 안전하다.

응답 shape(projection)는 각 인터페이스가 자기 계약대로 만든다 — REST는 stock 포함,
MCP 카탈로그 리소스는 stock 제외로 **계약이 서로 다르다**(중복 구현이 아니라 의도된 차이).
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session, joinedload

from app.db.models import Product


@dataclass(frozen=True)
class ProductView:
    """세션 독립 상품 뷰. 관계까지 해석 완료된 값 객체."""

    product_code: str
    name: str
    category: str
    price: int
    stock: int | None  # 재고 레코드가 없으면 None


def list_products(db: Session) -> list[ProductView]:
    """상품 전체를 product_code 오름차순으로 반환한다.

    product_code는 unique라 정렬이 완전히 결정론적이다. inventory는 joinedload로 한 번에
    가져와 N+1과 지연 로딩을 함께 없앤다.
    """
    rows = (
        db.query(Product)
        .options(joinedload(Product.inventory))
        .order_by(Product.product_code)
        .all()
    )
    return [
        ProductView(
            product_code=p.product_code,
            name=p.name,
            category=p.category,
            price=p.price,
            stock=p.inventory.stock if p.inventory else None,
        )
        for p in rows
    ]
