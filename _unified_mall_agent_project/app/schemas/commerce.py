"""커머스 API Pydantic 스키마."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=4, max_length=100)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProductResponse(BaseModel):
    product_code: str
    name: str
    category: str
    price: int
    stock: int | None = None


class OrderLineRequest(BaseModel):
    product_code: str
    quantity: int = Field(gt=0)


class OrderCreateRequest(BaseModel):
    items: list[OrderLineRequest] = Field(min_length=1)


class OrderItemResponse(BaseModel):
    product_name: str
    unit_price: int
    quantity: int


class OrderResponse(BaseModel):
    order_no: str
    status: str
    total_amount: int
    items: list[OrderItemResponse]


class PaymentCreateRequest(BaseModel):
    order_no: str
    method: str = Field(min_length=1)  # 금액은 서버가 주문 합계에서 계산


class PaymentResponse(BaseModel):
    order_no: str
    amount: int
    method: str
    status: str
