# app/schemas.py
# API 요청과 응답 데이터 구조를 정의하는 Pydantic 스키마 파일입니다.

from datetime import datetime  # 응답에 날짜와 시간을 포함하기 위해 사용합니다.
from decimal import Decimal  # 금액을 소수점 오차 없이 다루기 위해 사용합니다.
from pydantic import BaseModel, Field  # 데이터 검증 모델과 필드 조건을 정의하기 위해 사용합니다.


class UserCreate(BaseModel):
    # 회원가입 요청 데이터 구조입니다.
    username: str = Field(..., min_length=3, max_length=50, description="로그인 아이디")  # 아이디 길이를 검증합니다.
    password: str = Field(..., min_length=4, max_length=100, description="로그인 비밀번호")  # 비밀번호 길이를 검증합니다.
    name: str = Field(..., min_length=1, max_length=50, description="회원 이름")  # 이름 길이를 검증합니다.


class UserResponse(BaseModel):
    # 회원가입 성공 후 반환할 회원 정보 구조입니다.
    id: int  # 회원 고유 번호입니다.
    username: str  # 로그인 아이디입니다.
    name: str  # 회원 이름입니다.
    created_at: datetime  # 가입 시각입니다.

    model_config = {"from_attributes": True}  # SQLAlchemy ORM 객체를 Pydantic 응답으로 변환할 수 있게 합니다.


class TokenResponse(BaseModel):
    # 로그인 성공 후 반환할 JWT 토큰 응답 구조입니다.
    access_token: str  # API 인증에 사용할 액세스 토큰입니다.
    token_type: str = "bearer"  # Swagger 인증 방식에서 사용하는 토큰 타입입니다.


class BoardCreate(BaseModel):
    # 게시글 등록 요청 데이터 구조입니다.
    title: str = Field(..., min_length=1, max_length=200, description="게시글 제목")  # 제목 필수 입력 조건입니다.
    content: str = Field(..., min_length=1, description="게시글 내용")  # 내용 필수 입력 조건입니다.


class BoardUpdate(BaseModel):
    # 게시글 수정 요청 데이터 구조입니다.
    title: str = Field(..., min_length=1, max_length=200, description="수정할 게시글 제목")  # 수정 제목입니다.
    content: str = Field(..., min_length=1, description="수정할 게시글 내용")  # 수정 내용입니다.


class BoardListResponse(BaseModel):
    # 게시글 전체 조회에서 사용할 간단 응답 구조입니다.
    id: int  # 게시글 번호입니다.
    title: str  # 게시글 제목입니다.
    view_count: int  # 게시글 조회수입니다.
    writer_name: str  # 작성자 이름입니다.
    created_at: datetime  # 작성 시각입니다.

    model_config = {"from_attributes": True}  # ORM 객체 기반 변환을 허용합니다.


class BoardDetailResponse(BaseModel):
    # 게시글 상세 조회에서 사용할 응답 구조입니다.
    id: int  # 게시글 번호입니다.
    title: str  # 게시글 제목입니다.
    content: str  # 게시글 내용입니다.
    view_count: int  # 게시글 조회수입니다.
    writer_id: int  # 작성자 회원 번호입니다.
    writer_name: str  # 작성자 이름입니다.
    created_at: datetime  # 작성 시각입니다.
    updated_at: datetime  # 수정 시각입니다.

    model_config = {"from_attributes": True}  # ORM 객체 기반 변환을 허용합니다.


# =====================================================================
# 메뉴(메뉴정보) 스키마 - CRUD
# =====================================================================


class MenuCreate(BaseModel):
    # 메뉴 등록 요청 데이터 구조입니다.
    name: str = Field(..., min_length=1, max_length=100, description="메뉴 이름")  # 메뉴 이름 필수 입력 조건입니다.
    description: str | None = Field(None, max_length=255, description="메뉴 설명")  # 메뉴 설명은 선택 입력입니다.
    price: Decimal = Field(..., gt=0, description="메뉴 단가(0보다 커야 함)")  # 단가는 0보다 커야 합니다.
    is_available: bool = Field(True, description="판매 가능 여부")  # 기본값은 판매 가능입니다.


class MenuUpdate(BaseModel):
    # 메뉴 수정 요청 데이터 구조입니다. 전달된 값만 부분 수정합니다.
    name: str | None = Field(None, min_length=1, max_length=100, description="수정할 메뉴 이름")  # 수정할 이름입니다.
    description: str | None = Field(None, max_length=255, description="수정할 메뉴 설명")  # 수정할 설명입니다.
    price: Decimal | None = Field(None, gt=0, description="수정할 메뉴 단가")  # 수정할 단가입니다.
    is_available: bool | None = Field(None, description="수정할 판매 가능 여부")  # 수정할 판매 여부입니다.


class MenuResponse(BaseModel):
    # 메뉴 조회 응답 구조입니다.
    id: int  # 메뉴 번호입니다.
    name: str  # 메뉴 이름입니다.
    description: str | None  # 메뉴 설명입니다.
    price: Decimal  # 메뉴 단가입니다.
    is_available: bool  # 판매 가능 여부입니다.
    created_at: datetime  # 등록 시각입니다.
    updated_at: datetime  # 수정 시각입니다.

    model_config = {"from_attributes": True}  # ORM 객체 기반 변환을 허용합니다.


# =====================================================================
# 주문(주문내역) 스키마 - CRUD
# =====================================================================


class OrderItemCreate(BaseModel):
    # 주문 요청에 포함되는 개별 주문 항목입니다.
    menu_id: int = Field(..., description="주문할 메뉴 번호")  # 어떤 메뉴를 주문하는지 지정합니다.
    quantity: int = Field(..., gt=0, description="주문 수량(1개 이상)")  # 수량은 1개 이상이어야 합니다.


class OrderCreate(BaseModel):
    # 주문 등록 요청 데이터 구조입니다.
    items: list[OrderItemCreate] = Field(..., min_length=1, description="주문 항목 목록(1개 이상)")  # 최소 1개 항목이 필요합니다.


class OrderItemResponse(BaseModel):
    # 주문 상세 항목 응답 구조입니다.
    id: int  # 주문 상세 번호입니다.
    menu_id: int  # 주문한 메뉴 번호입니다.
    menu_name: str  # 주문 시점의 메뉴 이름입니다.
    unit_price: Decimal  # 주문 시점의 단가입니다.
    quantity: int  # 주문 수량입니다.
    line_total: Decimal  # 단가 x 수량 합계입니다.

    model_config = {"from_attributes": True}  # ORM 객체 기반 변환을 허용합니다.


class OrderResponse(BaseModel):
    # 주문 조회 응답 구조입니다.
    id: int  # 주문 번호입니다.
    user_id: int  # 주문한 회원 번호입니다.
    status: str  # 주문 상태입니다.(PENDING/PAID/CANCELLED)
    total_price: Decimal  # 주문 합계 금액입니다.
    created_at: datetime  # 주문 생성 시각입니다.
    items: list[OrderItemResponse]  # 주문에 포함된 상세 항목 목록입니다.

    model_config = {"from_attributes": True}  # ORM 객체 기반 변환을 허용합니다.


# =====================================================================
# 결제(결재정보) 스키마 - CRUD
# =====================================================================


class PaymentCreate(BaseModel):
    # 결제 요청 데이터 구조입니다.
    order_id: int = Field(..., description="결제할 주문 번호")  # 어떤 주문을 결제하는지 지정합니다.
    method: str = Field(..., description="결제 수단(CARD/CASH/POINT)")  # 결제 수단을 지정합니다.


class PaymentResponse(BaseModel):
    # 결제 조회 응답 구조입니다.
    id: int  # 결제 번호입니다.
    order_id: int  # 결제 대상 주문 번호입니다.
    amount: Decimal  # 결제 금액입니다.
    method: str  # 결제 수단입니다.
    status: str  # 결제 상태입니다.
    paid_at: datetime  # 결제 완료 시각입니다.

    model_config = {"from_attributes": True}  # ORM 객체 기반 변환을 허용합니다.
