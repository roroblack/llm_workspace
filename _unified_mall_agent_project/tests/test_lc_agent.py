"""LangChain 에이전트 계층 테스트 (구조/결정론, 모델 없음)."""

import json

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.agent.lc_agent import _extract_steps, _final_answer, run_langchain_agent
from app.agent.lc_tools import build_tools
from app.core.config import Settings
from app.core.errors import ConfigError
from app.core.llm_clients import get_langchain_chat
from app.db.database import SessionLocal


def test_get_langchain_chat_local_builds():
    s = Settings(_env_file=None, LLM_PROVIDER="local")
    chat = get_langchain_chat(s)  # 생성만
    assert chat is not None


def test_get_langchain_chat_openai_no_key_raises():
    s = Settings(_env_file=None, LLM_PROVIDER="openai", OPENAI_API_KEY=None)
    with pytest.raises(ConfigError):
        get_langchain_chat(s)


def test_get_langchain_chat_gemini_no_key_raises():
    s = Settings(_env_file=None, LLM_PROVIDER="gemini", GOOGLE_API_KEY=None)
    with pytest.raises(ConfigError):
        get_langchain_chat(s)


def test_extract_steps_and_final_answer():
    messages = [
        HumanMessage(content="P0001 가격?"),
        AIMessage(
            content="",
            tool_calls=[{"name": "get_price", "args": {"product_code": "P0001"}, "id": "c1"}],
        ),
        ToolMessage(
            content=json.dumps({"ok": True, "price": 79000}, ensure_ascii=False),
            tool_call_id="c1",
            name="get_price",
        ),
        AIMessage(content="가격은 79000원입니다."),
    ]
    steps = _extract_steps(messages)
    assert len(steps) == 1
    assert steps[0].action == "get_price"
    assert steps[0].action_input == {"product_code": "P0001"}
    assert steps[0].observation["price"] == 79000
    assert _final_answer(messages) == "가격은 79000원입니다."


def test_agent_constructs_without_invoke():
    """create_agent가 로컬 chat + 도구로 그래프를 구성하는지 (호출 없이 구조 확인)."""
    from langchain.agents import create_agent

    db = SessionLocal()
    try:
        chat = get_langchain_chat(Settings(_env_file=None, LLM_PROVIDER="local"))
        agent = create_agent(chat, build_tools(db))
        assert agent is not None
        assert hasattr(agent, "invoke")
    finally:
        db.close()


def test_get_langchain_chat_empty_local_model_raises(monkeypatch):
    s = Settings(_env_file=None, LLM_PROVIDER="local", LOCAL_MODEL="")
    with pytest.raises(ConfigError):
        get_langchain_chat(s)


class _FakeAgent:
    def __init__(self, result=None, exc=None):
        self._result = result
        self._exc = exc

    def invoke(self, _input, config=None):
        if self._exc:
            raise self._exc
        return self._result


def _patch_create_agent(monkeypatch, fake):
    import langchain.agents as lca

    monkeypatch.setattr(lca, "create_agent", lambda *a, **k: fake)


def test_run_langchain_agent_extracts_steps(monkeypatch):
    result = {
        "messages": [
            HumanMessage(content="가격?"),
            AIMessage(
                content="",
                tool_calls=[{"name": "get_price", "args": {"product_code": "P0001"}, "id": "c1"}],
            ),
            ToolMessage(
                content=json.dumps({"ok": True, "price": 79000}),
                tool_call_id="c1",
                name="get_price",
            ),
            AIMessage(content="79000원입니다."),
        ]
    }
    _patch_create_agent(monkeypatch, _FakeAgent(result=result))
    db = SessionLocal()
    try:
        res = run_langchain_agent("가격?", db, model=object())
        assert res.stopped_by == "final_answer"
        assert len(res.steps) == 1
        assert res.steps[0].action == "get_price"
        assert res.answer == "79000원입니다."
    finally:
        db.close()


def test_run_langchain_agent_recursion_to_max_steps(monkeypatch):
    class GraphRecursionError(Exception):
        pass

    _patch_create_agent(monkeypatch, _FakeAgent(exc=GraphRecursionError("limit")))
    db = SessionLocal()
    try:
        res = run_langchain_agent("x", db, model=object())
        assert res.stopped_by == "max_steps"
    finally:
        db.close()


def test_run_langchain_agent_connection_to_infra_error(monkeypatch):
    from app.core.errors import InfraError

    class APIConnectionError(Exception):
        pass

    _patch_create_agent(monkeypatch, _FakeAgent(exc=APIConnectionError("down")))
    db = SessionLocal()
    try:
        with pytest.raises(InfraError):
            run_langchain_agent("x", db, model=object())
    finally:
        db.close()


def test_lc_chat_router(client, monkeypatch):
    from app.agent.schemas import AgentResponse, AgentStep
    from app.routers import agent as agent_router

    def fake(question, db, recursion_limit=8):
        return AgentResponse(
            answer="ok",
            steps=[AgentStep(step=1, action="get_price", action_input={}, observation={"ok": True})],
            stopped_by="final_answer",
        )

    monkeypatch.setattr(agent_router, "run_langchain_agent", fake)
    r = client.post("/api/agent/lc-chat", json={"question": "가격?", "max_steps": 2})
    assert r.status_code == 200
    assert r.json()["stopped_by"] == "final_answer"


@pytest.mark.llm
def test_lc_agent_live():
    """로컬/실키 라이브 스모크 (수동, CI 제외)."""
    db = SessionLocal()
    try:
        res = run_langchain_agent("P0001 가격 알려줘", db, recursion_limit=6)
        assert isinstance(res.answer, str)
    finally:
        db.close()
