"""SQLAlchemy ORM 모델을 정의하는 모듈입니다.

작성자와 게시글을 외래키(ForeignKey) + relationship으로 연결한
정규화된 관계형 설계를 사용합니다.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """회원 정보를 저장하는 테이블입니다."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # 회원이 작성한 게시글 목록입니다.
    # cascade="all, delete-orphan" 이므로 회원이 삭제되면 그 회원의 게시글도 함께 삭제됩니다.
    posts: Mapped[list["Board"]] = relationship(
        "Board",
        back_populates="writer",
        cascade="all, delete-orphan",
    )


class Board(Base):
    """자유게시판 게시글을 저장하는 테이블입니다."""

    __tablename__ = "boards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # 작성자 users.id를 참조하는 외래키입니다.
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # 게시글 작성자(User) 정보를 가져오기 위한 관계입니다.
    writer: Mapped["User"] = relationship("User", back_populates="posts")
