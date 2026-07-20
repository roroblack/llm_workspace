"""커머스 승인 루프 유스케이스 (Phase 6, 프레임워크 무의존).

미리보기(PreviewOrder, 읽기전용·DB변경0)와 승인(PlaceOrder, 멱등키 필수·원자적 주문)을
**분리된 유스케이스**로 강제한다 → "미리보기 전 DB변경 0", "승인 없는 주문 0"을 구조로 보장.
검증 실패는 삼키지 않고 명시적 타입 에러(무폴백). SQLAlchemy/FastAPI를 import하지 않는다.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from app.core.errors import ConflictErr, ValidationErr


# --- DTO -------------------------------------------------------------------
@dataclass(frozen=True)
class OrderLine:
    product_code: str
    quantity: int


@dataclass(frozen=True)
class ProductInfo:
    product_id: int
    product_code: str
    name: str
    price: int


@dataclass(frozen=True)
class PreviewLine:
    product_code: str
    name: str | None  # 미상품이면 None
    unit_price: int | None
    quantity: int
    subtotal: int  # 미상품/재고부족이어도 계산 가능한 만큼(unit_price*qty), 미상품이면 0
    available: int | None
    sufficient: bool


@dataclass(frozen=True)
class OrderPreview:
    lines: list[PreviewLine]
    total: int
    feasible: bool  # 모든 라인이 존재+재고충분이면 True
    issues: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PlacedItem:
    product_name: str
    unit_price: int
    quantity: int


@dataclass(frozen=True)
class PlacedOrder:
    order_no: str
    status: str
    total: int
    items: list[PlacedItem]


@dataclass(frozen=True)
class IdempotentHit:
    order: PlacedOrder
    request_hash: str


# --- Ports -----------------------------------------------------------------
@runtime_checkable
class CatalogPort(Protocol):
    """카탈로그 읽기(미리보기용). 구현: SqlCatalog, FakeCatalog(테스트)."""

    def get_product(self, code: str) -> ProductInfo | None: ...
    def get_stock(self, product_id: int) -> int: ...


@runtime_checkable
class OrderRepositoryPort(Protocol):
    """주문 멱등 조회 + 원자적 생성. 구현: SqlOrderRepository, FakeOrderRepo(테스트)."""

    def find_by_idempotency_key(self, user_id: int, key: str) -> IdempotentHit | None: ...

    def place(
        self, user_id: int, lines: list[OrderLine], key: str, request_hash: str
    ) -> PlacedOrder:
        """원자적: 재검증(미상품→NotFoundErr, 재고부족·수량≤0→ValidationErr) + 주문/항목
        스냅샷 + 재고차감 + 멱등레코드(key,hash,order_id) 기록을 **한 트랜잭션**으로.
        키 unique 경합 시 기존 주문 재조회로 수렴(중복 생성 금지)."""
        ...


# --- 순수 헬퍼 -------------------------------------------------------------
def request_fingerprint(lines: list[OrderLine]) -> str:
    """요청 라인의 정규 지문(SHA-256). 같은 키·다른 payload 탐지용.

    상품코드 정렬 후 코드별 수량 합산 → 순서·중복 무관하게 동일 주문은 동일 지문.
    상품코드에 구분자가 있어도 모호하지 않도록 JSON 배열로 직렬화(Codex 지적).
    """
    agg: dict[str, int] = {}
    for ln in lines:
        agg[ln.product_code] = agg.get(ln.product_code, 0) + ln.quantity
    canonical = json.dumps(
        [[code, agg[code]] for code in sorted(agg)], separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# --- Use cases -------------------------------------------------------------
class PreviewOrder:
    """미리보기 유스케이스 — 읽기전용. DB를 변경하지 않는다."""

    def __init__(self, catalog: CatalogPort) -> None:
        self._catalog = catalog

    def __call__(self, lines: list[OrderLine]) -> OrderPreview:
        if not lines:
            raise ValidationErr("주문 항목이 비어 있습니다.")

        preview_lines: list[PreviewLine] = []
        issues: list[str] = []
        total = 0
        feasible = True
        demanded: dict[int, int] = {}  # product_id → 누적 요청 수량(중복 라인 합산)
        for ln in lines:
            if ln.quantity <= 0:
                raise ValidationErr("수량은 1 이상이어야 합니다.")
            product = self._catalog.get_product(ln.product_code)
            if product is None:
                feasible = False
                issues.append(f"상품 없음: {ln.product_code}")
                preview_lines.append(
                    PreviewLine(ln.product_code, None, None, ln.quantity, 0, None, False)
                )
                continue
            stock = self._catalog.get_stock(product.product_id)
            # 같은 상품이 여러 라인이면 누적 수요로 충분성 판단(단일 라인만 보면 과다판매 미탐).
            demanded[product.product_id] = demanded.get(product.product_id, 0) + ln.quantity
            sufficient = stock >= demanded[product.product_id]
            if not sufficient:
                feasible = False
                issues.append(
                    f"재고 부족: {product.name} (누적 요청 {demanded[product.product_id]}, 재고 {stock})"
                )
            subtotal = product.price * ln.quantity
            total += subtotal
            preview_lines.append(
                PreviewLine(
                    product_code=ln.product_code,
                    name=product.name,
                    unit_price=product.price,
                    quantity=ln.quantity,
                    subtotal=subtotal,
                    available=stock,
                    sufficient=sufficient,
                )
            )
        return OrderPreview(lines=preview_lines, total=total, feasible=feasible, issues=issues)


class PlaceOrder:
    """승인(주문 생성) 유스케이스 — 멱등키 필수, 원자적."""

    def __init__(self, orders: OrderRepositoryPort) -> None:
        self._orders = orders

    def __call__(self, user_id: int, lines: list[OrderLine], idempotency_key: str) -> PlacedOrder:
        if not idempotency_key:
            # 멱등키를 서버가 몰래 생성하면 재시도마다 새 주문 → 멱등 무력화(무폴백 위반).
            raise ValidationErr("Idempotency-Key 헤더가 필요합니다.")
        if not lines:
            raise ValidationErr("주문 항목이 비어 있습니다.")
        # 멱등 조회 전에 수량을 검증한다. 지문은 순수량 합산이라 A×2,A×-1(=순1)이 A×1과 같은
        # 지문이 되어 잘못된 요청이 재생될 수 있으므로, 조회 전에 음수·0을 거부한다(Codex 지적).
        for ln in lines:
            if ln.quantity <= 0:
                raise ValidationErr("수량은 1 이상이어야 합니다.")

        fingerprint = request_fingerprint(lines)
        hit = self._orders.find_by_idempotency_key(user_id, idempotency_key)
        if hit is not None:
            if hit.request_hash != fingerprint:
                raise ConflictErr("같은 Idempotency-Key로 다른 주문을 보낼 수 없습니다.")
            return hit.order  # 멱등 재생: 신규 쓰기·재고차감 없음
        return self._orders.place(user_id, lines, idempotency_key, fingerprint)
