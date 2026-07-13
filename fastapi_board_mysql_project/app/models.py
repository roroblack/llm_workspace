# app/models.py
# MySQL 테이블과 매핑되는 SQLAlchemy ORM 모델을 정의합니다.

from datetime import datetime  # 각 테이블의 생성/수정 시각 기본값을 만들기 위해 사용합니다.
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text, Boolean  # 테이블 컬럼 타입입니다.
from sqlalchemy.orm import relationship  # 모델 간(회원-주문-결제 등) 관계를 표현하기 위해 사용합니다.
from app.database import Base  # 모든 ORM 모델이 상속받는 Base 클래스를 가져옵니다.


class User(Base):
    # users 테이블과 매핑되는 회원 모델입니다. (회원정보 저장)
    __tablename__ = "users"  # 실제 MySQL 테이블 이름을 지정합니다.

    id = Column(Integer, primary_key=True, index=True)  # 회원 고유 번호이며 기본키입니다.
    username = Column(String(50), unique=True, index=True, nullable=False)  # 로그인 아이디이며 중복을 허용하지 않습니다.
    password_hash = Column(String(255), nullable=False)  # 원문 비밀번호가 아니라 해시된 비밀번호를 저장합니다.
    name = Column(String(50), nullable=False)  # 회원 이름을 저장합니다.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # 회원 가입 시각을 UTC 기준으로 저장합니다.

    posts = relationship("Board", back_populates="writer", cascade="all, delete-orphan")  # 회원이 작성한 게시글 목록 관계입니다.
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")  # 회원이 등록한 주문 목록 관계입니다.


class Board(Base):
    # boards 테이블과 매핑되는 자유게시글 모델입니다.
    __tablename__ = "boards"  # 실제 MySQL 테이블 이름을 지정합니다.

    id = Column(Integer, primary_key=True, index=True)  # 게시글 고유 번호이며 기본키입니다.
    title = Column(String(200), nullable=False)  # 게시글 제목을 저장합니다.
    content = Column(Text, nullable=False)  # 게시글 본문을 저장합니다.
    view_count = Column(Integer, default=0, nullable=False)  # 상세 조회 시 1씩 증가하는 조회수입니다.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 작성자 users.id를 참조하는 외래키입니다.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # 게시글 작성 시각입니다.
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)  # 수정 시 자동 갱신되는 시각입니다.

    writer = relationship("User", back_populates="posts")  # 게시글 작성자 정보를 가져오기 위한 관계입니다.


class Menu(Base):
    # menus 테이블과 매핑되는 메뉴 모델입니다. (메뉴정보 저장)
    __tablename__ = "menus"  # 실제 MySQL 테이블 이름을 지정합니다.

    id = Column(Integer, primary_key=True, index=True)  # 메뉴 고유 번호이며 기본키입니다.
    name = Column(String(100), unique=True, index=True, nullable=False)  # 메뉴 이름이며 중복을 허용하지 않습니다.
    description = Column(String(255), nullable=True)  # 메뉴 설명입니다. 선택 입력값입니다.
    price = Column(Numeric(10, 2), nullable=False)  # 메뉴 단가입니다. 금액은 소수점 오차를 피하려고 Numeric으로 저장합니다.
    is_available = Column(Boolean, default=True, nullable=False)  # 판매 가능 여부입니다. False면 주문할 수 없습니다.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # 메뉴 등록 시각입니다.
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)  # 메뉴 수정 시각입니다.

    order_items = relationship("OrderItem", back_populates="menu")  # 이 메뉴가 포함된 주문 상세 목록 관계입니다.


class Order(Base):
    # orders 테이블과 매핑되는 주문(주문내역) 모델입니다.
    __tablename__ = "orders"  # 실제 MySQL 테이블 이름을 지정합니다.

    id = Column(Integer, primary_key=True, index=True)  # 주문 고유 번호이며 기본키입니다.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 주문한 회원 users.id를 참조하는 외래키입니다.
    status = Column(String(20), default="PENDING", nullable=False)  # 주문 상태입니다. PENDING/PAID/CANCELLED 등을 저장합니다.
    total_price = Column(Numeric(10, 2), default=0, nullable=False)  # 주문 상세 금액의 합계이며 서비스에서 계산해 저장합니다.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # 주문 생성 시각입니다.

    user = relationship("User", back_populates="orders")  # 주문한 회원 정보를 가져오기 위한 관계입니다.
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")  # 주문에 포함된 상세 항목 목록입니다.
    payment = relationship("Payment", back_populates="order", uselist=False, cascade="all, delete-orphan")  # 주문 1건당 결제 1건(1:1) 관계입니다.


class OrderItem(Base):
    # order_items 테이블과 매핑되는 주문 상세(주문내역 항목) 모델입니다.
    __tablename__ = "order_items"  # 실제 MySQL 테이블 이름을 지정합니다.

    id = Column(Integer, primary_key=True, index=True)  # 주문 상세 고유 번호이며 기본키입니다.
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)  # 소속 주문 orders.id를 참조하는 외래키입니다.
    menu_id = Column(Integer, ForeignKey("menus.id"), nullable=False)  # 주문한 메뉴 menus.id를 참조하는 외래키입니다.
    menu_name = Column(String(100), nullable=False)  # 주문 시점의 메뉴 이름을 스냅샷으로 저장합니다.
    unit_price = Column(Numeric(10, 2), nullable=False)  # 주문 시점의 메뉴 단가를 스냅샷으로 저장합니다.
    quantity = Column(Integer, nullable=False)  # 주문 수량입니다.
    line_total = Column(Numeric(10, 2), nullable=False)  # 단가 x 수량으로 계산한 항목 합계입니다.

    order = relationship("Order", back_populates="items")  # 소속 주문 정보를 가져오기 위한 관계입니다.
    menu = relationship("Menu", back_populates="order_items")  # 주문한 메뉴 정보를 가져오기 위한 관계입니다.


class Payment(Base):
    # payments 테이블과 매핑되는 결제(결재정보) 모델입니다.
    __tablename__ = "payments"  # 실제 MySQL 테이블 이름을 지정합니다.

    id = Column(Integer, primary_key=True, index=True)  # 결제 고유 번호이며 기본키입니다.
    order_id = Column(Integer, ForeignKey("orders.id"), unique=True, nullable=False)  # 결제 대상 주문 외래키이며 1:1이므로 유니크입니다.
    amount = Column(Numeric(10, 2), nullable=False)  # 실제 결제 금액입니다. 주문 합계와 일치해야 합니다.
    method = Column(String(20), nullable=False)  # 결제 수단입니다. CARD/CASH/POINT 등을 저장합니다.
    status = Column(String(20), default="PAID", nullable=False)  # 결제 상태입니다. PAID/CANCELLED 등을 저장합니다.
    paid_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # 결제 완료 시각입니다.

    order = relationship("Order", back_populates="payment")  # 결제 대상 주문 정보를 가져오기 위한 관계입니다.
