# app/models.py
# MySQL 테이블과 매핑되는 SQLAlchemy ORM 모델을 정의합니다.

from datetime import datetime  # 게시글 작성일과 수정일의 기본값을 만들기 위해 사용합니다.
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text  # 테이블 컬럼 타입을 정의하기 위해 사용합니다.
from sqlalchemy.orm import relationship  # User와 Board 사이의 관계를 표현하기 위해 사용합니다.
from app.database import Base  # 모든 ORM 모델이 상속받는 Base 클래스를 가져옵니다.


class User(Base):
    # users 테이블과 매핑되는 회원 모델입니다.
    __tablename__ = "users"  # 실제 MySQL 테이블 이름을 지정합니다.

    id = Column(Integer, primary_key=True, index=True)  # 회원 고유 번호이며 기본키입니다.
    username = Column(String(50), unique=True, index=True, nullable=False)  # 로그인 아이디이며 중복을 허용하지 않습니다.
    password_hash = Column(String(255), nullable=False)  # 원문 비밀번호가 아니라 해시된 비밀번호를 저장합니다.
    name = Column(String(50), nullable=False)  # 회원 이름을 저장합니다.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # 회원 가입 시각을 UTC 기준으로 저장합니다.

    posts = relationship("Board", back_populates="writer", cascade="all, delete-orphan")  # 회원이 작성한 게시글 목록 관계입니다.


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
