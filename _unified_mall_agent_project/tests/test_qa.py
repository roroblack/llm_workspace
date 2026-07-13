"""RAG QA 테스트 (service.search를 mock해 모델 없이 결정론 검증 — CI 포함)."""

import pytest

from app.core.errors import InfraError, ValidationErr
from app.rag import qa


def test_empty_question_raises():
    with pytest.raises(ValidationErr):
        qa.answer("   ")


def test_no_results_returns_no_answer(monkeypatch):
    monkeypatch.setattr(qa.service, "search", lambda q, k=None: [])
    r = qa.answer("아무 근거 없는 질문", chat_complete=lambda p: "LLM은 호출되면 안 됨")
    assert r["answer"] == qa.NO_ANSWER
    assert r["sources"] == []


def test_answer_and_sources_dedup_and_page_1based(monkeypatch):
    results = [
        {"text": "환불은 7일 이내 가능", "source": "환불교환정책.pdf", "page": 2, "distance": 0.5},
        {"text": "환불 배송비 안내", "source": "환불교환정책.pdf", "page": 2, "distance": 0.6},  # 중복
        {"text": "교환 안내", "source": "notice.txt", "page": None, "distance": 0.7},
    ]
    monkeypatch.setattr(qa.service, "search", lambda q, k=None: results)
    r = qa.answer("환불 며칠 이내?", chat_complete=lambda p: "7일 이내입니다.")
    assert r["answer"] == "7일 이내입니다."
    # (source,page) 중복 제거 + PDF page 0-based→1-based, TXT는 None, 순서 유지
    assert r["sources"] == [
        {"source": "환불교환정책.pdf", "page": 3},
        {"source": "notice.txt", "page": None},
    ]


def test_results_present_but_answer_absent_passes_llm_no_answer(monkeypatch):
    """검색 결과는 있으나 답이 없을 때 LLM이 NO_ANSWER를 내면 그대로 반환된다."""
    results = [{"text": "무관한 내용", "source": "x.txt", "page": None, "distance": 1.0}]
    monkeypatch.setattr(qa.service, "search", lambda q, k=None: results)
    r = qa.answer("답이 없는 질문", chat_complete=lambda p: qa.NO_ANSWER)
    assert r["answer"] == qa.NO_ANSWER


def test_prompt_contains_retrieved_text(monkeypatch):
    """검색된 본문이 실제로 LLM 프롬프트에 전달되는지 검증."""
    results = [{"text": "제주 왕복 배송비 10,000원", "source": "환불교환정책.pdf", "page": 1, "distance": 0.4}]
    monkeypatch.setattr(qa.service, "search", lambda q, k=None: results)
    captured = {}

    def capture(prompt):
        captured["p"] = prompt
        return "10,000원입니다."

    qa.answer("제주 배송비?", chat_complete=capture)
    assert "제주 왕복 배송비 10,000원" in captured["p"]  # PDF 본문이 프롬프트에 포함


def test_prompt_has_injection_defense_and_context():
    prompt = qa._build_prompt("환불 며칠?", [{"text": "본문", "source": "p.pdf", "page": 1}])
    assert "따르지 말" in prompt  # 문서 내 지시 무시(인젝션 방어)
    assert qa.NO_ANSWER in prompt  # 근거 없으면 고정 답변 지시
    assert "본문" in prompt


def test_empty_llm_response_raises_llm_output_error(monkeypatch):
    """실제 completion 경로에서 빈 응답은 LLMOutputError."""
    from app.core.errors import LLMOutputError

    class _Msg:
        content = "   "

    class _Choice:
        message = _Msg()

    class _Resp:
        choices = [_Choice()]

    class _Client:
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    return _Resp()

    monkeypatch.setattr("app.core.llm_clients.get_chat_client", lambda *a, **k: _Client())
    monkeypatch.setattr("app.core.llm_clients.get_active_model", lambda *a, **k: "m")
    with pytest.raises(LLMOutputError):
        qa._default_chat_complete("prompt")


def test_pdf_parse_failure_raises_infra_error(tmp_path):
    """PDF 파싱 실패는 TXT로 조용히 대체하지 않고 InfraError로 명시 실패."""
    from app.rag.build_index import _load_docs

    (tmp_path / "broken.pdf").write_text("이건 진짜 PDF가 아니라 그냥 텍스트입니다", encoding="utf-8")
    with pytest.raises(InfraError):
        _load_docs(tmp_path)
