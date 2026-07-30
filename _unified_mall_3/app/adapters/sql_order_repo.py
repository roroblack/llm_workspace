"""SqlOrderRepository — OrderRepositoryPort의 SQLAlchemy 구현(Phase 6).

멱등 조회 + 원자적 주문 생성(재검증·스냅샷·재고차감·멱등레코드 한 트랜잭션). 멱등키 unique
경합은 기존 주문 재조회로 수렴한다(중복 주문 금지). 검증 실패는 롤백 후 명시적 타입 에러(무폴백).
"""

from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.commerce import (
    IdempotentHit,
    OrderLine,
    PlacedItem,
    PlacedOrder,
)
from app.core.errors import ConflictErr, InfraError, NotFoundErr, ValidationErr
from app.db.models import Inventory, Order, OrderIdempotency, OrderItem, Product


def _is_unique_violation(exc: IntegrityError) -> bool:
    """IntegrityError가 unique 제약 위반인지 판별(SQLite·PostgreSQL). FK/NOT NULL 등과 구분해
    멱등키 경합만 수렴 처리하기 위함(Codex 지적: 다른 무결성 오류 오분류 금지)."""
    orig = getattr(exc, "orig", None)
    sqlstate = getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)
    if sqlstate == "23505":  # PostgreSQL unique_violation
        return True
    return "UNIQUE constraint failed" in str(orig)  # SQLite 메시지 시그니처


def _new_order_no() -> str:
    return "O" + uuid.uuid4().hex[:11].upper()


def _to_placed(order: Order) -> PlacedOrder:
    return PlacedOrder(
        order_no=order.order_no,
        status=order.status,
        total=order.total_amount,
        items=[
            PlacedItem(product_name=i.product_name, unit_price=i.unit_price, quantity=i.quantity)
            for i in order.items
        ],
    )


class SqlOrderRepository:
    """OrderRepositoryPort 구현."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def find_by_idempotency_key(self, user_id: int, key: str) -> IdempotentHit | None:
        rec = (
            self._db.query(OrderIdempotency)
            .filter(
                OrderIdempotency.user_id == user_id,
                OrderIdempotency.idempotency_key == key,
            )
            .first()
        )
        if rec is None:
            return None
        order = self._db.query(Order).filter(Order.id == rec.order_id).first()
        if order is None:
            # 멱등레코드는 있는데 주문이 없다 = 내부 데이터 불변식 위반(클라이언트 404 아님).
            raise InfraError("멱등 레코드에 해당하는 주문을 찾을 수 없습니다.")
        return IdempotentHit(order=_to_placed(order), request_hash=rec.request_hash)

    def place(
        self, user_id: int, lines: list[OrderLine], key: str, request_hash: str
    ) -> PlacedOrder:
        try:
            order = Order(
                order_no=_new_order_no(), user_id=user_id, status="PENDING", total_amount=0
            )
            total = 0
            for ln in lines:
                if ln.quantity <= 0:
                    raise ValidationErr("수량은 1 이상이어야 합니다.")
                product = (
                    self._db.query(Product)
                    .filter(Product.product_code == ln.product_code)
                    .first()
                )
                if product is None:
                    raise NotFoundErr(f"상품을 찾을 수 없습니다: {ln.product_code}")
                inv = (
                    self._db.query(Inventory)
                    .filter(Inventory.product_id == product.id)
                    .first()
                )
                if inv is None:
                    # 상품은 있는데 재고 레코드가 없다 = 데이터 불변식 위반. 0으로 조용히 때우지 않는다.
                    raise InfraError(f"재고 레코드 없음(불변식 위반): {ln.product_code}")
                # 조건부 원자 차감: stock>=qty일 때만 감소. 동시 요청 초과판매(lost update) 방지.
                decremented = (
                    self._db.query(Inventory)
                    .filter(Inventory.product_id == product.id, Inventory.stock >= ln.quantity)
                    .update(
                        {Inventory.stock: Inventory.stock - ln.quantity},
                        synchronize_session=False,
                    )
                )
                if decremented != 1:
                    inv_now = (
                        self._db.query(Inventory)
                        .filter(Inventory.product_id == product.id)
                        .first()
                    )
                    if inv_now is None:
                        # 차감 사이 재고 레코드 소멸 = 불변식 위반(None.stock 접근 금지).
                        raise InfraError(f"재고 레코드 없음(불변식 위반): {ln.product_code}")
                    raise ValidationErr(
                        f"재고 부족: {product.name} (요청 {ln.quantity}, 재고 {inv_now.stock})"
                    )
                order.items.append(
                    OrderItem(
                        product_id=product.id,
                        product_name=product.name,  # 주문시점 스냅샷
                        unit_price=product.price,  # 주문시점 스냅샷
                        quantity=ln.quantity,
                    )
                )
                total += product.price * ln.quantity

            order.total_amount = total
            self._db.add(order)
            self._db.flush()  # order.id 확보

            # 멱등레코드 삽입만 savepoint로 격리 → 여기서 난 IntegrityError는 **확실히**
            # (user_id, idempotency_key) unique 충돌이다(다른 무결성 오류를 오분류하지 않음).
            try:
                with self._db.begin_nested():
                    self._db.add(
                        OrderIdempotency(
                            user_id=user_id,
                            idempotency_key=key,
                            request_hash=request_hash,
                            order_id=order.id,
                        )
                    )
                    self._db.flush()
            except IntegrityError as exc:
                self._db.rollback()
                if not _is_unique_violation(exc):
                    # FK·NOT NULL·CHECK 등 다른 무결성 오류는 멱등 경합이 아니다 → 삼키지 않고 전파.
                    raise
                # 동시 요청이 같은 키로 먼저 커밋됨. 이 주문 시도를 전부 롤백하고 승자로 수렴.
                hit = self.find_by_idempotency_key(user_id, key)
                if hit is None:
                    raise InfraError("멱등키 충돌이나 기존 레코드를 찾을 수 없습니다.")
                if hit.request_hash != request_hash:
                    # 같은 키·다른 payload가 동시에 경합 → 패자는 409.
                    raise ConflictErr("같은 Idempotency-Key로 다른 주문을 보낼 수 없습니다.")
                return hit.order  # 멱등 재생

            self._db.commit()  # 주문+항목+재고차감+멱등레코드 원자적 커밋
            self._db.refresh(order)
            return _to_placed(order)
        except Exception:
            self._db.rollback()
            raise
