"""RAG 라우터: 검색 / 요약."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.application.answer_question import NO_ANSWER, AnswerResult
from app.composition import build_answer_question
from app.db.database import get_db
from app.obs.events import record_event
from app.obs.knowledge_gaps import record_knowledge_gap
from app.rag.service import search
from app.rag.summarize import summarize_text

router = APIRouter(prefix="/api/rag", tags=["rag"])


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)
    source: str | None = None


class SummarizeRequest(BaseModel):
    text: str = Field(min_length=1)


class QARequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)


@router.post("/search")
def rag_search(body: SearchRequest) -> dict:
    return {"results": search(body.query, k=body.top_k, source=body.source)}


def _to_response(result: AnswerResult) -> dict:
    # 변환은 rag_view 1벌만 사용한다 — MCP와 응답이 어긋나지 않도록(Phase 8 parity).
    from app.adapters.rag_view import answer_to_dict

    return answer_to_dict(result)


@router.post("/qa")
def rag_qa(body: QARequest, db: Session = Depends(get_db)) -> dict:
    """질문 → 근거 기반 답변 + 출처 인용 (환각 억제). AnswerQuestion 유스케이스 경유.

    관측성(NFR-OBS-01): 처리 결과를 run_events에 trace_id와 함께 기록한다(원문 저장 금지, 요약만).
    """
    use_case = build_answer_question(top_k=body.top_k)
    result = use_case(body.question)
    record_event(
        db,
        kind="rag_query",
        detail={"top_k": body.top_k, "source_count": len(result.sources)},
    )
    # 지식보강 큐(Phase 9): 근거를 못 찾아 답하지 못한 질문을 모은다 = 문서 보강 대상.
    # 유스케이스는 순수(DB 무지)라 **인터페이스 계층인 여기서** 기록한다(Clean Arch 경계).
    if result.answer == NO_ANSWER:
        record_knowledge_gap(db, body.question)
    return _to_response(result)


@router.post("/summarize")
def rag_summarize(body: SummarizeRequest) -> dict:
    return {"summary": summarize_text(body.text)}
