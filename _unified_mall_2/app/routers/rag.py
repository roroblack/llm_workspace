"""RAG 라우터: 검색 / 요약."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.application.answer_question import AnswerResult
from app.composition import build_answer_question
from app.db.database import get_db
from app.obs.events import record_event
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


def _page(locator: str | None) -> int | None:
    """Citation.locator(문자열) → 레거시 HTTP 응답의 page(int|None) 형태 유지."""
    return int(locator) if locator and locator.isdigit() else None


def _to_response(result: AnswerResult) -> dict:
    return {
        "answer": result.answer,
        "sources": [
            {"source": c.source, "page": _page(c.locator)} for c in result.sources
        ],
    }


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
    return _to_response(result)


@router.post("/summarize")
def rag_summarize(body: SummarizeRequest) -> dict:
    return {"summary": summarize_text(body.text)}
