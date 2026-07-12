"""주문 라우터 (인증 필요)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.db.database import get_db
from app.db.models import Order, User
from app.schemas.commerce import (
    OrderCreateRequest,
    OrderItemResponse,
    OrderResponse,
)
from app.services import order_service

router = APIRouter(prefix="/api/orders", tags=["orders"])


def _to_response(order: Order) -> OrderResponse:
    return OrderResponse(
        order_no=order.order_no,
        status=order.status,
        total_amount=order.total_amount,
        items=[
            OrderItemResponse(
                product_name=i.product_name, unit_price=i.unit_price, quantity=i.quantity
            )
            for i in order.items
        ],
    )


@router.post("", response_model=OrderResponse)
def create_order(
    body: OrderCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderResponse:
    lines = [{"product_code": it.product_code, "quantity": it.quantity} for it in body.items]
    order = order_service.create_order(db, user, lines)
    return _to_response(order)


@router.get("", response_model=list[OrderResponse])
def list_orders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[OrderResponse]:
    return [_to_response(o) for o in order_service.list_orders(db, user)]


@router.get("/{order_no}", response_model=OrderResponse)
def get_order(
    order_no: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderResponse:
    return _to_response(order_service.get_order(db, user, order_no))
