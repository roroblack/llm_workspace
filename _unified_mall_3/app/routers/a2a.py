"""A2A 라우터 — 에이전트 발견(카드) + 위임 메시지.

- GET  /api/a2a/agents  : 등록된 전문 에이전트 카드 목록(발견/discovery).
- POST /api/a2a/message : 대상 전문 에이전트에 작업 위임(delegation).

운영/통합 표면(MCP와 유사)이라 고객 공개 포트에는 싣지 않는다(main.py의 운영 라우터 그룹).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.a2a.cards import list_agent_cards
from app.a2a.gateway import delegate_to_agent
from app.db.database import get_db

router = APIRouter(prefix="/api/a2a", tags=["a2a"])


@router.get("/agents")
def agent_cards() -> dict[str, object]:
    """등록된 전문 에이전트 카드 목록(A2A 발견)."""
    return {"agents": list_agent_cards()}


class A2AMessageRequest(BaseModel):
    target_agent: str = Field(min_length=1, description="위임 대상 에이전트(order/catalog/knowledge/recommend-agent)")
    message: str = Field(min_length=1, description="위임할 자연어 메시지")


@router.post("/message")
def a2a_message(body: A2AMessageRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    """대상 전문 에이전트에 작업을 위임한다. 미등록 에이전트/빈 입력은 무폴백 422."""
    result = delegate_to_agent(db, body.target_agent, body.message)
    return {"target_agent": body.target_agent, "result": result}
