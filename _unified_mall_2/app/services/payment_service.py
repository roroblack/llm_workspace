"""결제 서비스: 주문 결제(검증) / 조회.

결제 생성 + 주문 PAID 전환은 한 트랜잭션으로 처리한다. 금액은 서버가 주문
합계에서 계산한다 (Codex 합의).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.errors import ForbiddenErr, NotFoundErr, ValidationErr
from app.db.models import Order, Payment, User


def pay_order(db: Session, user: User, order_no: str, method: str) -> Payment:
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if order is None:
        raise NotFoundErr("주문을 찾을 수 없습니다.")
    if order.user_id != user.id:
        raise ForbiddenErr("본인의 주문만 결제할 수 있습니다.")
    if order.status == "PAID" or order.payment is not None:
        raise ValidationErr("이미 결제된 주문입니다.")

    try:
        payment = Payment(
            order_id=order.id,
            amount=order.total_amount,  # 서버가 주문 합계에서 계산
            method=method,
            status="PAID",
        )
        order.status = "PAID"
        db.add(payment)
        db.commit()  # 결제+주문 PAID 원자적 커밋
        db.refresh(payment)
        return payment
    except Exception:
        db.rollback()
        raise


def get_payment(db: Session, user: User, order_no: str) -> Payment:
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if order is None:
        raise NotFoundErr("주문을 찾을 수 없습니다.")
    if order.user_id != user.id:
        raise ForbiddenErr("본인의 결제만 조회할 수 있습니다.")
    if order.payment is None:
        raise NotFoundErr("결제 내역이 없습니다.")
    return order.payment
