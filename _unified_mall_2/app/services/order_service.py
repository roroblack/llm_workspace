"""주문 서비스: 생성(재고검증·스냅샷·합계·재고차감) / 조회.

주문 생성 + 재고 차감 + 주문항목 저장은 한 트랜잭션(한 commit)으로 처리한다
(Codex 합의: 원자성).
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.errors import ForbiddenErr, NotFoundErr, ValidationErr
from app.db.models import Inventory, Order, OrderItem, Product, User


def _new_order_no() -> str:
    return "O" + uuid.uuid4().hex[:11].upper()


def create_order(db: Session, user: User, lines: list[dict]) -> Order:
    """lines: [{"product_code": str, "quantity": int}, ...]"""
    order = Order(order_no=_new_order_no(), user_id=user.id, status="PENDING", total_amount=0)
    total = 0
    try:
        for line in lines:
            code = line["product_code"]
            qty = int(line["quantity"])
            if qty <= 0:
                raise ValidationErr("수량은 1 이상이어야 합니다.")

            product = db.query(Product).filter(Product.product_code == code).first()
            if product is None:
                raise NotFoundErr(f"상품을 찾을 수 없습니다: {code}")

            inv = db.query(Inventory).filter(Inventory.product_id == product.id).first()
            available = inv.stock if inv else 0
            if available < qty:
                raise ValidationErr(
                    f"재고 부족: {product.name} (요청 {qty}, 재고 {available})"
                )

            # 주문시점 단가/상품명 스냅샷
            order.items.append(
                OrderItem(
                    product_id=product.id,
                    product_name=product.name,
                    unit_price=product.price,
                    quantity=qty,
                )
            )
            total += product.price * qty
            inv.stock -= qty  # 재고 차감

        order.total_amount = total
        db.add(order)
        db.commit()  # 주문+항목+재고차감 원자적 커밋
        db.refresh(order)
        return order
    except Exception:
        db.rollback()
        raise


def list_orders(db: Session, user: User) -> list[Order]:
    return db.query(Order).filter(Order.user_id == user.id).order_by(Order.id.desc()).all()


def get_order(db: Session, user: User, order_no: str) -> Order:
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if order is None:
        raise NotFoundErr("주문을 찾을 수 없습니다.")
    if order.user_id != user.id:
        raise ForbiddenErr("본인의 주문만 조회할 수 있습니다.")
    return order
