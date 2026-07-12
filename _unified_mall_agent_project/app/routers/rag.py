"""RAG 라우터: 검색 / 요약."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.rag.service import search
from app.rag.summarize import summarize_text

router = APIRouter(prefix="/api/rag", tags=["rag"])


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)
    source: str | None = None


class SummarizeRequest(BaseModel):
    text: str = Field(min_length=1)


@router.post("/search")
def rag_search(body: SearchRequest) -> dict:
    return {"results": search(body.query, k=body.top_k, source=body.source)}


@router.post("/summarize")
def rag_summarize(body: SummarizeRequest) -> dict:
    return {"summary": summarize_text(body.text)}
