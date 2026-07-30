"""주문 조회 서비스 (읽기 경로).

주문 **생성**은 Phase 6에서 `app/application/commerce.py`(PreviewOrder/PlaceOrder) +
`app/adapters/sql_order_repo.py`로 옮겼다. 여기 있던 레거시 `create_order`는 라우터가
유스케이스를 쓰게 된 뒤 호출자가 0이 되어 Phase 8에서 삭제했다(구현 2벌 방지).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.errors import ForbiddenErr, NotFoundErr
from app.db.models import Order, User


def list_orders(db: Session, user: User) -> list[Order]:
    return db.query(Order).filter(Order.user_id == user.id).order_by(Order.id.desc()).all()


def get_order(db: Session, user: User, order_no: str) -> Order:
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if order is None:
        raise NotFoundErr("주문을 찾을 수 없습니다.")
    if order.user_id != user.id:
        raise ForbiddenErr("본인의 주문만 조회할 수 있습니다.")
    return order
