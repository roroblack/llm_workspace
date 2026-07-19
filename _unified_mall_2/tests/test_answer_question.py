"""Phase 1 — AnswerQuestion 유스케이스 계약 테스트(Fake만, 외부 의존 0).

REQ-RAG-04/05, TEST-RAG-PORT-001~004.
"""

from __future__ import annotations

import pytest

from app.application.answer_question import NO_ANSWER, AnswerQuestion
from app.application.ports import Evidence
from app.core.errors import InfraError, LLMOutputError, ValidationErr
from tests.fakes.fake_model import FakeModelGateway
from tests.fakes.fake_retriever import FakeRetriever


def _ev() -> list[Evidence]:
    return [Evidence(content="환불은 7일 이내 가능", source="환불교환정책.pdf", locator="3", score=0.9, backend="fake")]


def test_req_rag_04_answer_with_sources():  # TEST-RAG-PORT-001
    uc = AnswerQuestion(FakeRetriever(_ev()), FakeModelGateway(reply="7일 이내입니다"))
    r = uc("환불 기한?")
    assert r.answer == "7일 이내입니다"
    assert [(c.source, c.locator) for c in r.sources] == [("환불교환정책.pdf", "3")]


def test_req_rag_05_abstention_when_no_evidence():  # TEST-RAG-PORT-002
    model = FakeModelGateway(reply="이 답은 나오면 안 됨")
    uc = AnswerQuestion(FakeRetriever([]), model)
    r = uc("근거 없는 질문")
    assert r.answer == NO_ANSWER
    assert r.sources == []
    assert model.prompts == []  # 근거 없으면 모델 호출 안 함(생성 금지)


def test_empty_question_raises_validation():  # TEST-RAG-PORT-003
    uc = AnswerQuestion(FakeRetriever(_ev()), FakeModelGateway())
    with pytest.raises(ValidationErr):
        uc("   ")


def test_model_infra_error_propagates():  # TEST-RAG-PORT-004
    uc = AnswerQuestion(FakeRetriever(_ev()), FakeModelGateway(raises=InfraError("LLM down")))
    with pytest.raises(InfraError):
        uc("환불 기한?")


def test_empty_reply_is_llm_output_error():
    uc = AnswerQuestion(FakeRetriever(_ev()), FakeModelGateway(reply="   "))
    with pytest.raises(LLMOutputError):
        uc("환불 기한?")


def test_citations_dedup_and_order():
    ev = [
        Evidence("a", "policy.pdf", "2", 0.9, "fake"),
        Evidence("b", "policy.pdf", "2", 0.8, "fake"),  # 중복
        Evidence("c", "notice.txt", None, 0.7, "fake"),
    ]
    uc = AnswerQuestion(FakeRetriever(ev), FakeModelGateway(reply="ok"))
    r = uc("q")
    assert [(c.source, c.locator) for c in r.sources] == [("policy.pdf", "2"), ("notice.txt", None)]


def test_top_k_passed_to_retriever():
    retr = FakeRetriever(_ev())
    uc = AnswerQuestion(retr, FakeModelGateway(reply="ok"), top_k=5)
    uc("환불?")
    assert retr.calls[0][1] == 5  # k
