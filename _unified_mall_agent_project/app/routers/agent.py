"""ReAct 에이전트 라우터."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agent.lc_agent import run_langchain_agent
from app.agent.react import run_react_agent
from app.agent.schemas import AgentResponse
from app.db.database import get_db

router = APIRouter(prefix="/api/agent", tags=["agent"])


class AgentChatRequest(BaseModel):
    question: str = Field(min_length=1)
    max_steps: int = Field(default=3, ge=1, le=6)


@router.post("/chat", response_model=AgentResponse)
def agent_chat(body: AgentChatRequest, db: Session = Depends(get_db)) -> AgentResponse:
    """수동 ReAct 루프 (학습 baseline)."""
    return run_react_agent(body.question, db, max_steps=body.max_steps)


@router.post("/lc-chat", response_model=AgentResponse)
def agent_lc_chat(body: AgentChatRequest, db: Session = Depends(get_db)) -> AgentResponse:
    """LangChain 자동 ReAct (Phase 3.5). 운영 경로 후보."""
    return run_langchain_agent(body.question, db, recursion_limit=body.max_steps * 2 + 2)
