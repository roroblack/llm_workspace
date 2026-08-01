# app/routers/payments.py
# 결제(결재정보) API를 정의하는 라우터 파일입니다.

from fastapi import APIRouter, Depends, HTTPException, status  # 라우터, 의존성 주입, HTTP 오류를 사용합니다.
from sqlalchemy.orm import Session  # DB 세션 타입 힌트에 사용합니다.
from app.database import get_db  # DB 세션 의존성 함수입니다.
from app.models import User  # 로그인 사용자 타입 힌트에 사용합니다.
from app.schemas import PaymentCreate, PaymentResponse  # 결제 요청/응답 스키마입니다.
from app.security import get_current_user  # 로그인 사용자 확인 의존성 함수입니다.
from app.services import payment_service  # 결제 비즈니스 로직 서비스 계층입니다.

router = APIRouter(prefix="/payments", tags=["결제"] )  # /payments로 시작하는 결제 API 그룹을 만듭니다.


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(payment_data: PaymentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 로그인한 사용자가 주문을 결제하는 API입니다.
    try:  # 결제 검증 실패 시 서비스가 예외를 던집니다.
        return payment_service.create_payment(db, current_user, payment_data)  # 결제를 생성해 반환합니다.
    except PermissionError as exc:  # 본인 주문이 아닌 경우입니다.
        raise HTTPException(status_code=403, detail=str(exc))  # 403 권한 오류로 변환합니다.
    except ValueError as exc:  # 주문 미존재/중복 결제/잘못된 결제수단입니다.
        raise HTTPException(status_code=400, detail=str(exc))  # 400 오류로 변환합니다.


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 결제 상세를 조회하는 API입니다. 본인 결제만 볼 수 있습니다.
    payment = payment_service.get_payment(db, payment_id)  # 결제를 조회합니다.
    if not payment:  # 없으면 404 오류를 반환합니다.
        raise HTTPException(status_code=404, detail="결제 정보를 찾을 수 없습니다.")  # 미존재 오류입니다.
    if payment.order.user_id != current_user.id:  # 본인 결제가 아니면 조회를 막습니다.
        raise HTTPException(status_code=403, detail="본인 결제만 조회할 수 있습니다.")  # 권한 오류입니다.
    return payment  # 결제 상세를 반환합니다.
