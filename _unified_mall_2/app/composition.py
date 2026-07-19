"""Composition root — 어댑터를 유스케이스에 조립·주입한다(Interface가 유스케이스만 보게).

Phase 1: RAG 질문 유스케이스를 FAISS 검색 + 레지스트리 모델 게이트웨이로 조립.
이후 Phase에서 pgvector/GraphRAG 어댑터로 교체 지점이 된다(설정 기반 선택은 Phase 3).
"""

from __future__ import annotations

from app.adapters.faiss_retriever import FaissRetriever
from app.adapters.llm_gateway import LlmGateway
from app.application.answer_question import AnswerQuestion


def build_answer_question(top_k: int | None = None) -> AnswerQuestion:
    return AnswerQuestion(retriever=FaissRetriever(), model=LlmGateway(), top_k=top_k)
