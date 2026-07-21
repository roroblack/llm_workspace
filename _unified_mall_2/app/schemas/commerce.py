"""커머스 API Pydantic 스키마."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=4, max_length=100)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginResponse(BaseModel):
    """로그인 응답 — 얼굴 미등록이면 access_token 발급, 등록됐으면 얼굴 2차인증 요구.

    face_2fa_required=True인 경우 access_token은 없고 challenge_token(단명 pre2fa)만 있다.
    프론트는 challenge_token으로 `/auth/login/face`를 호출해 최종 access_token을 받는다.
    """

    face_2fa_required: bool = False
    access_token: str | None = None
    token_type: str = "bearer"
    challenge_token: str | None = None


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


class PreviewLineResponse(BaseModel):
    product_code: str
    name: str | None
    unit_price: int | None
    quantity: int
    subtotal: int
    available: int | None
    sufficient: bool


class OrderPreviewResponse(BaseModel):
    lines: list[PreviewLineResponse]
    total: int
    feasible: bool
    issues: list[str]


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
