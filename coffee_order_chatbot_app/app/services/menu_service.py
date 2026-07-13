# app/services/menu_service.py
# 메뉴(메뉴정보) 관련 비즈니스 로직을 담당하는 서비스 계층입니다. (CRUD)

from sqlalchemy.orm import Session  # DB 세션 타입 힌트에 사용합니다.
from app.models import Menu  # menus 테이블 ORM 모델입니다.
from app.schemas import MenuCreate, MenuUpdate  # 메뉴 생성/수정 요청 스키마입니다.


def get_menu(db: Session, menu_id: int) -> Menu | None:
    # 메뉴 번호로 단일 메뉴를 조회합니다. 없으면 None입니다.
    return db.query(Menu).filter(Menu.id == menu_id).first()  # 첫 번째 일치 메뉴를 반환합니다.


def list_menus(db: Session, only_available: bool = False) -> list[Menu]:
    # 메뉴 전체 목록을 조회합니다. only_available=True면 판매 가능 메뉴만 반환합니다.
    query = db.query(Menu)  # 기본 메뉴 조회 쿼리입니다.
    if only_available:  # 판매 가능 메뉴만 필터링할지 확인합니다.
        query = query.filter(Menu.is_available.is_(True))  # 판매 가능 메뉴만 남깁니다.
    return query.order_by(Menu.id.asc()).all()  # 번호 오름차순으로 전체를 반환합니다.


def create_menu(db: Session, menu_data: MenuCreate) -> Menu:
    # 신규 메뉴를 생성합니다. 이름이 중복되면 ValueError를 발생시킵니다.
    existing = db.query(Menu).filter(Menu.name == menu_data.name).first()  # 동일 이름 메뉴가 있는지 확인합니다.
    if existing:  # 이미 존재하면 생성을 막습니다.
        raise ValueError("이미 존재하는 메뉴 이름입니다.")  # 중복 오류를 발생시킵니다.

    new_menu = Menu(  # DB에 저장할 새 Menu ORM 객체를 만듭니다.
        name=menu_data.name,  # 메뉴 이름입니다.
        category=menu_data.category,  # 메뉴 분류입니다.
        description=menu_data.description,  # 메뉴 설명입니다.
        price=menu_data.price,  # 메뉴 단가입니다.
        stock=menu_data.stock,  # 재고 수량입니다.
        is_available=menu_data.is_available,  # 판매 가능 여부입니다.
    )
    db.add(new_menu)  # 세션에 추가합니다.
    db.commit()  # INSERT를 DB에 반영합니다.
    db.refresh(new_menu)  # 자동 생성 값을 객체에 반영합니다.
    return new_menu  # 생성된 메뉴를 반환합니다.


def update_menu(db: Session, menu_id: int, menu_data: MenuUpdate) -> Menu | None:
    # 메뉴를 부분 수정합니다. 대상이 없으면 None을 반환합니다.
    menu = get_menu(db, menu_id)  # 수정 대상 메뉴를 조회합니다.
    if not menu:  # 없으면 None을 반환합니다.
        return None  # 라우터에서 404 처리합니다.

    update_fields = menu_data.model_dump(exclude_unset=True)  # 전달된 필드만 딕셔너리로 추립니다.
    for field, value in update_fields.items():  # 전달된 필드를 하나씩 반영합니다.
        setattr(menu, field, value)  # 해당 속성을 새 값으로 설정합니다.

    db.commit()  # UPDATE를 DB에 반영합니다.
    db.refresh(menu)  # 갱신된 값을 객체에 반영합니다.
    return menu  # 수정된 메뉴를 반환합니다.


def delete_menu(db: Session, menu_id: int) -> bool:
    # 메뉴를 삭제합니다. 대상이 없으면 False를 반환합니다.
    menu = get_menu(db, menu_id)  # 삭제 대상 메뉴를 조회합니다.
    if not menu:  # 없으면 삭제하지 않습니다.
        return False  # 실패를 알립니다.
    db.delete(menu)  # 삭제를 준비합니다.
    db.commit()  # DELETE를 DB에 반영합니다.
    return True  # 삭제 성공을 알립니다.


def seed_menus(db: Session, menu_list: list[dict]) -> int:
    # 앱 최초 실행 시 메뉴 테이블이 비어 있으면 기본 커피 메뉴를 등록합니다.
    # menu_data.COFFEE_MENU 형식의 딕셔너리 리스트를 받아 DB에 저장하고 등록 개수를 반환합니다.
    if db.query(Menu).count() > 0:  # 이미 메뉴가 있으면 중복 등록하지 않습니다.
        return 0  # 새로 등록한 개수 0을 반환합니다.

    created = 0  # 새로 등록한 메뉴 개수입니다.
    for item in menu_list:  # 기본 메뉴 데이터를 하나씩 순회합니다.
        menu = Menu(  # 기본 메뉴 딕셔너리를 Menu ORM 객체로 변환합니다.
            name=item["name"],  # 메뉴 이름입니다.
            category=item.get("category", "coffee"),  # 메뉴 분류입니다.
            description=item.get("description"),  # 메뉴 설명입니다.
            price=item["price"],  # 메뉴 단가입니다.
            stock=100,  # 초기 재고를 넉넉히 100으로 설정합니다.
            is_available=True,  # 기본적으로 판매 가능으로 등록합니다.
        )
        db.add(menu)  # 세션에 추가합니다.
        created += 1  # 등록 개수를 늘립니다.
    db.commit()  # 모든 기본 메뉴 INSERT를 한 번에 반영합니다.
    return created  # 새로 등록한 메뉴 개수를 반환합니다.
