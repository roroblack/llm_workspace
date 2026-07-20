"""주문 라우터 (인증 필요)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.composition import build_place_order, build_preview_order
from app.application.commerce import OrderLine
from app.db.database import get_db
from app.db.models import Order, User
from app.schemas.commerce import (
    OrderCreateRequest,
    OrderItemResponse,
    OrderPreviewResponse,
    OrderResponse,
    PreviewLineResponse,
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


@router.post("/preview", response_model=OrderPreviewResponse)
def preview_order(
    body: OrderCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderPreviewResponse:
    """주문 미리보기(읽기전용, DB 변경 없음). 승인 전 확인용."""
    lines = [OrderLine(product_code=it.product_code, quantity=it.quantity) for it in body.items]
    preview = build_preview_order(db)(lines)
    return OrderPreviewResponse(
        lines=[
            PreviewLineResponse(
                product_code=pl.product_code,
                name=pl.name,
                unit_price=pl.unit_price,
                quantity=pl.quantity,
                subtotal=pl.subtotal,
                available=pl.available,
                sufficient=pl.sufficient,
            )
            for pl in preview.lines
        ],
        total=preview.total,
        feasible=preview.feasible,
        issues=preview.issues,
    )


@router.post("", response_model=OrderResponse)
def create_order(
    body: OrderCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> OrderResponse:
    """주문 생성(승인). Idempotency-Key 헤더 필수 — 동일 키 재요청은 같은 주문을 재생(멱등)."""
    lines = [OrderLine(product_code=it.product_code, quantity=it.quantity) for it in body.items]
    placed = build_place_order(db)(user.id, lines, idempotency_key or "")
    return OrderResponse(
        order_no=placed.order_no,
        status=placed.status,
        total_amount=placed.total,
        items=[
            OrderItemResponse(
                product_name=i.product_name, unit_price=i.unit_price, quantity=i.quantity
            )
            for i in placed.items
        ],
    )


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
