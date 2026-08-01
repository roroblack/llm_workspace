# app/services/order_service.py
# 주문(주문내역) 관련 비즈니스 로직을 담당하는 서비스 계층입니다.

from decimal import Decimal  # 금액 계산을 소수점 오차 없이 처리하기 위해 사용합니다.
from sqlalchemy.orm import Session  # DB 세션 타입 힌트에 사용합니다.
from app.models import Menu, Order, OrderItem, User  # 주문 처리에 필요한 ORM 모델입니다.
from app.schemas import OrderCreate  # 주문 생성 요청 스키마입니다.


def create_order(db: Session, user: User, order_data: OrderCreate) -> Order:
    # 로그인 회원의 주문을 생성합니다.
    # 메뉴 존재/판매 여부를 검증하고, 주문 시점의 단가/이름을 스냅샷으로 저장하며, 합계를 계산합니다.
    order = Order(user_id=user.id, status="PENDING", total_price=Decimal("0"))  # 우선 빈 주문을 만듭니다.

    total = Decimal("0")  # 주문 합계 누적 변수입니다.
    for item in order_data.items:  # 요청에 담긴 주문 항목을 하나씩 처리합니다.
        menu = db.query(Menu).filter(Menu.id == item.menu_id).first()  # 주문한 메뉴를 조회합니다.
        if not menu:  # 메뉴가 없으면 잘못된 주문입니다.
            raise ValueError(f"존재하지 않는 메뉴입니다. (menu_id={item.menu_id})")  # 오류를 발생시킵니다.
        if not menu.is_available:  # 판매 중지 메뉴는 주문할 수 없습니다.
            raise ValueError(f"현재 판매하지 않는 메뉴입니다. (menu={menu.name})")  # 오류를 발생시킵니다.

        line_total = menu.price * item.quantity  # 항목 합계 = 단가 x 수량입니다.
        total += line_total  # 주문 합계에 누적합니다.

        order.items.append(  # 주문에 상세 항목을 추가합니다.
            OrderItem(
                menu_id=menu.id,  # 메뉴 번호입니다.
                menu_name=menu.name,  # 주문 시점의 메뉴 이름 스냅샷입니다.
                unit_price=menu.price,  # 주문 시점의 단가 스냅샷입니다.
                quantity=item.quantity,  # 주문 수량입니다.
                line_total=line_total,  # 항목 합계입니다.
            )
        )

    order.total_price = total  # 계산된 합계를 주문에 반영합니다.
    db.add(order)  # 주문(및 cascade로 상세 항목)을 세션에 추가합니다.
    db.commit()  # INSERT를 DB에 반영합니다.
    db.refresh(order)  # 자동 생성 값을 객체에 반영합니다.
    return order  # 생성된 주문을 반환합니다.


def get_order(db: Session, order_id: int) -> Order | None:
    # 주문 번호로 단일 주문을 조회합니다. 없으면 None입니다.
    return db.query(Order).filter(Order.id == order_id).first()  # 첫 번째 일치 주문을 반환합니다.


def list_orders_by_user(db: Session, user: User) -> list[Order]:
    # 특정 회원의 주문 내역을 최신순으로 조회합니다.
    return (
        db.query(Order)
        .filter(Order.user_id == user.id)  # 로그인 회원의 주문만 조회합니다.
        .order_by(Order.id.desc())  # 최신 주문이 먼저 오도록 정렬합니다.
        .all()  # 전체 목록을 반환합니다.
    )


def mark_order_paid(db: Session, order: Order) -> Order:
    # 주문 상태를 결제 완료(PAID)로 변경합니다. 결제 서비스에서 호출합니다.
    order.status = "PAID"  # 주문 상태를 결제 완료로 갱신합니다.
    db.commit()  # UPDATE를 DB에 반영합니다.
    db.refresh(order)  # 갱신된 값을 객체에 반영합니다.
    return order  # 갱신된 주문을 반환합니다.
