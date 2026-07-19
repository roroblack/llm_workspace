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


def build_graph_answer_question(top_k: int | None = None) -> AnswerQuestion:
    """GraphRAG: pgvector(문서 청크) + PG 그래프(정형 관계 사실)를 결합한 RAG.

    그래프 사실이 벡터 청크와 함께 근거로 들어가 관계 집계·비교 질의를 보강한다(Phase 5b).
    같은 RetrieverPort라 AnswerQuestion을 수정 없이 재사용.
    """
    from app.adapters.fusion_retriever import FusionRetriever
    from app.adapters.pg_graph_retriever import PgGraphRetriever
    from app.adapters.pgvector_retriever import PgVectorRetriever

    fusion = FusionRetriever([PgVectorRetriever(), PgGraphRetriever()])
    return AnswerQuestion(retriever=fusion, model=LlmGateway(), top_k=top_k)


def build_hybrid_answer_question(top_k: int | None = None, rerank: bool = False) -> AnswerQuestion:
    """Hybrid RAG: dense(pgvector) + lexical(pg_trgm)을 RRF로 결합(Phase 4).

    rerank=True면 결합 결과를 LLM-as-reranker로 재정렬(RerankedRetriever). 모두 같은
    RetrieverPort라 AnswerQuestion을 수정 없이 재사용. 정렬 순서는 그대로 근거로 들어간다.
    """
    from app.adapters.hybrid_retriever import HybridRetriever
    from app.adapters.pg_lexical_retriever import PgLexicalRetriever
    from app.adapters.pgvector_retriever import PgVectorRetriever

    model = LlmGateway()
    retriever = HybridRetriever([PgVectorRetriever(), PgLexicalRetriever()])
    if rerank:
        from app.adapters.reranker import LlmReranker, RerankedRetriever

        retriever = RerankedRetriever(retriever, LlmReranker(model))
    return AnswerQuestion(retriever=retriever, model=model, top_k=top_k)
