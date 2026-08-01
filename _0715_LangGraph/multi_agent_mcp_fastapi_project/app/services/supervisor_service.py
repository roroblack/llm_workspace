# -*- coding: utf-8 -*-
"""Supervisor가 라우팅, 전문 답변, MySQL 기록을 하나의 흐름으로 조정합니다."""
import json
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.repositories.consultation_repository import ConsultationRepository
from app.services.agent_service import AgentService
from app.services.router_service import route_hybrid, route_llm, route_rule

class SupervisorService:
    def __init__(self) -> None:
        self.agent_service = AgentService()
        self.repository = ConsultationRepository()

    def process(self, db: Session, question: str, router_type: str, provider: str | None) -> dict:
        selected_provider = provider or get_settings().llm_provider
        if router_type == "rule":
            route = route_rule(question)
        elif router_type == "llm":
            route = route_llm(question, selected_provider)
        else:
            route = route_hybrid(question, selected_provider)
        answer, evidence = self.agent_service.answer(question, route, selected_provider)
        row = self.repository.create(db, question=question, route=route, provider=selected_provider, answer=answer, evidence=json.dumps(evidence, ensure_ascii=False))
        return {"consultation_id": row.id, "route": route, "answer": answer, "evidence": evidence, "provider": selected_provider}
