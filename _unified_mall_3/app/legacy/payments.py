"""결제 라우터 (인증 필요)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.db.database import get_db
from app.db.models import Payment, User
from app.schemas.commerce import PaymentCreateRequest, PaymentResponse
from app.services import payment_service

router = APIRouter(prefix="/api/payments", tags=["payments"])


def _to_response(payment: Payment) -> PaymentResponse:
    return PaymentResponse(
        order_no=payment.order.order_no,
        amount=payment.amount,
        method=payment.method,
        status=payment.status,
    )


@router.post("", response_model=PaymentResponse)
def create_payment(
    body: PaymentCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PaymentResponse:
    payment = payment_service.pay_order(db, user, body.order_no, body.method)
    return _to_response(payment)


@router.get("/{order_no}", response_model=PaymentResponse)
def get_payment(
    order_no: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PaymentResponse:
    return _to_response(payment_service.get_payment(db, user, order_no))
