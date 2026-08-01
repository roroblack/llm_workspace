# -*- coding: utf-8 -*-
"""SQLAlchemy 기반 MySQL 연결과 세션 생명주기를 관리합니다."""
from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from app.core.config import get_settings

settings = get_settings()
# pool_pre_ping은 끊어진 MySQL 연결을 사용하기 전에 검사합니다.
engine = create_engine(settings.database_url, pool_pre_ping=True, pool_recycle=280, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

class Base(DeclarativeBase):
    """모든 ORM 모델이 상속하는 선언형 기본 클래스입니다."""


def get_db() -> Generator[Session, None, None]:
    """요청마다 DB 세션을 만들고 요청 종료 후 반드시 닫습니다."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """등록된 ORM 모델을 기준으로 누락된 테이블을 생성합니다."""
    from app.models import consultation  # noqa: F401
    Base.metadata.create_all(bind=engine)
