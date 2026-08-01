# -*- coding: utf-8 -*-
"""상담 질문, 라우팅 결과, 답변을 저장하는 MySQL ORM 모델입니다."""
from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base

class Consultation(Base):
    """한 번의 사용자 상담 실행 결과를 저장합니다."""
    __tablename__ = "consultations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    route: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
