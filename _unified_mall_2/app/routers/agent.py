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


class SupportCheckResponse(BaseModel):
    """근거 정합성 검사 결과. `verified` 단정이 아니라 '무엇을 누가 점검했는지'를 남긴다."""

    result: str  # supported / unsupported
    checked_by: str  # llm — 사람 검토 아님
    model: str
    reason: str


class CheckedChatResponse(BaseModel):
    answer: str
    support_check: SupportCheckResponse
    draft_blocked: bool
    steps: list[dict]
    stopped_by: str
    # 자기검증은 초안과 같은 모델의 자기 점검이라 독립 검증이 아니며 진실성을 보증하지 않는다.
    disclaimer: str = (
        "근거 정합성 검사만 수행했습니다(같은 모델의 자기 점검). "
        "사실의 진실성·완전성을 보증하지 않습니다."
    )


@router.post("/chat-verified", response_model=CheckedChatResponse)
def agent_chat_verified(
    body: AgentChatRequest, db: Session = Depends(get_db)
) -> CheckedChatResponse:
    """ReAct 에이전트 + CoT 자기검증(Phase 7). 미지지 초안은 차단된다."""
    from app.composition import build_chat_commerce

    result = build_chat_commerce(db, max_steps=body.max_steps)(body.question)
    sc = result.support_check
    return CheckedChatResponse(
        answer=result.answer,
        support_check=SupportCheckResponse(
            result=sc.result, checked_by=sc.checked_by, model=sc.model, reason=sc.reason
        ),
        draft_blocked=result.draft_blocked,
        steps=result.steps,
        stopped_by=result.stopped_by,
    )
