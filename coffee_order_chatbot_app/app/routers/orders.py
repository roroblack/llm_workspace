# app/routers/orders.py
# 주문(주문내역) API를 정의하는 라우터 파일입니다.

from fastapi import APIRouter, Depends, HTTPException, status  # 라우터, 의존성 주입, HTTP 오류를 사용합니다.
from sqlalchemy.orm import Session  # DB 세션 타입 힌트에 사용합니다.
from app.database import get_db  # DB 세션 의존성 함수입니다.
from app.models import User  # 로그인 사용자 타입 힌트에 사용합니다.
from app.schemas import OrderCreate, OrderResponse  # 주문 요청/응답 스키마입니다.
from app.security import get_current_user  # 로그인 사용자 확인 의존성 함수입니다.
from app.services import order_service  # 주문 비즈니스 로직 서비스 계층입니다.

router = APIRouter(prefix="/orders", tags=["주문"])  # /orders로 시작하는 주문 API 그룹을 만듭니다.


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(order_data: OrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 로그인한 사용자가 메뉴를 주문하는 API입니다.
    try:  # 메뉴 미존재/판매중지/재고부족 시 서비스가 ValueError를 던집니다.
        return order_service.create_order(db, current_user, order_data)  # 주문을 생성해 반환합니다.
    except ValueError as exc:  # 주문 항목 검증 실패입니다.
        raise HTTPException(status_code=400, detail=str(exc))  # 400 오류로 변환합니다.


@router.get("", response_model=list[OrderResponse])
def get_my_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 로그인한 사용자의 주문 내역을 조회하는 API입니다.
    return order_service.list_orders_by_user(db, current_user)  # 본인 주문 목록을 반환합니다.


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 주문 상세를 조회하는 API입니다. 본인 주문만 볼 수 있습니다.
    order = order_service.get_order(db, order_id)  # 주문을 조회합니다.
    if not order:  # 없으면 404 오류를 반환합니다.
        raise HTTPException(status_code=404, detail="주문을 찾을 수 없습니다.")  # 미존재 오류입니다.
    if order.user_id != current_user.id:  # 본인 주문이 아니면 조회를 막습니다.
        raise HTTPException(status_code=403, detail="본인 주문만 조회할 수 있습니다.")  # 권한 오류입니다.
    return order  # 주문 상세를 반환합니다.
