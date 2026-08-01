# -*- coding: utf-8 -*-
"""상담 이력에 대한 DB 접근을 서비스 계층에서 분리합니다."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.consultation import Consultation

class ConsultationRepository:
    def create(self, db: Session, *, question: str, route: str, provider: str, answer: str, evidence: str) -> Consultation:
        row = Consultation(question=question, route=route, provider=provider, answer=answer, evidence=evidence)
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def list_recent(self, db: Session, limit: int = 20) -> list[Consultation]:
        stmt = select(Consultation).order_by(Consultation.id.desc()).limit(limit)
        return list(db.scalars(stmt).all())
