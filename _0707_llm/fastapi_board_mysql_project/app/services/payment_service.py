# app/services/payment_service.py
# 결제(결재정보) 관련 비즈니스 로직을 담당하는 서비스 계층입니다.

from sqlalchemy.orm import Session  # DB 세션 타입 힌트에 사용합니다.
from app.models import Payment, User  # 결제 ORM 모델과 회원 모델입니다.
from app.schemas import PaymentCreate  # 결제 요청 스키마입니다.
from app.services import order_service  # 주문 조회/상태 변경을 위해 주문 서비스를 사용합니다.

ALLOWED_METHODS = {"CARD", "CASH", "POINT"}  # 허용되는 결제 수단 집합입니다.


def create_payment(db: Session, user: User, payment_data: PaymentCreate) -> Payment:
    # 주문에 대한 결제를 생성합니다.
    # 본인 주문 여부, 중복 결제 여부, 결제 수단, 주문 상태를 검증하고 주문을 결제 완료로 갱신합니다.
    order = order_service.get_order(db, payment_data.order_id)  # 결제 대상 주문을 조회합니다.
    if not order:  # 주문이 없으면 결제할 수 없습니다.
        raise ValueError("결제할 주문을 찾을 수 없습니다.")  # 오류를 발생시킵니다.
    if order.user_id != user.id:  # 본인 주문이 아니면 결제를 막습니다.
        raise PermissionError("본인 주문만 결제할 수 있습니다.")  # 권한 오류를 발생시킵니다.
    if payment_data.method not in ALLOWED_METHODS:  # 허용되지 않은 결제 수단을 막습니다.
        raise ValueError("결제 수단은 CARD, CASH, POINT 중 하나여야 합니다.")  # 오류를 발생시킵니다.
    if order.status == "PAID" or order.payment is not None:  # 이미 결제된 주문은 중복 결제를 막습니다.
        raise ValueError("이미 결제가 완료된 주문입니다.")  # 오류를 발생시킵니다.

    payment = Payment(  # DB에 저장할 새 Payment ORM 객체를 만듭니다.
        order_id=order.id,  # 결제 대상 주문 번호입니다.
        amount=order.total_price,  # 결제 금액은 주문 합계와 동일합니다.
        method=payment_data.method,  # 결제 수단입니다.
        status="PAID",  # 결제 상태를 완료로 설정합니다.
    )
    db.add(payment)  # 세션에 추가합니다.
    order_service.mark_order_paid(db, order)  # 주문 상태를 PAID로 갱신하고 commit합니다.
    db.refresh(payment)  # 자동 생성 값을 결제 객체에 반영합니다.
    return payment  # 생성된 결제를 반환합니다.


def get_payment(db: Session, payment_id: int) -> Payment | None:
    # 결제 번호로 단일 결제를 조회합니다. 없으면 None입니다.
    return db.query(Payment).filter(Payment.id == payment_id).first()  # 첫 번째 일치 결제를 반환합니다.


def get_payment_by_order(db: Session, order_id: int) -> Payment | None:
    # 주문 번호로 해당 주문의 결제를 조회합니다. 없으면 None입니다.
    return db.query(Payment).filter(Payment.order_id == order_id).first()  # 첫 번째 일치 결제를 반환합니다.
