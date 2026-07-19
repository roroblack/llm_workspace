"""LangChain 자동 ReAct 에이전트 (Phase 3.5).

langchain.agents.create_agent(CompiledStateGraph)로 자동화. 결과 메시지에서
도구 호출/관찰을 AgentStep으로 추출해 수동 ReAct와 동일한 AgentResponse로 반환한다.

제약: 로컬 Gemma는 tool_calls 미지원 → 로컬에선 도구 실행 없이 최종답변만. 라이브
tool-calling 검증은 최종 실키(OpenAI/Gemini).
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.agent.lc_tools import build_tools
from app.agent.react import DEFAULT_SYSTEM_PROMPT
from app.agent.schemas import AgentResponse, AgentStep
from app.core.errors import InfraError


def _extract_steps(messages: list[Any]) -> list[AgentStep]:
    """메시지 목록에서 (도구 호출 → 관찰) 쌍을 AgentStep으로 추출."""
    # tool_call_id → (name, args)
    call_meta: dict[str, tuple[str, dict]] = {}
    for m in messages:
        tool_calls = getattr(m, "tool_calls", None)
        if tool_calls:
            for tc in tool_calls:
                call_meta[tc.get("id", "")] = (tc.get("name", ""), tc.get("args", {}) or {})

    steps: list[AgentStep] = []
    step_no = 0
    for m in messages:
        if m.__class__.__name__ == "ToolMessage":
            step_no += 1
            name, args = call_meta.get(getattr(m, "tool_call_id", ""), (getattr(m, "name", ""), {}))
            try:
                observation = json.loads(m.content)
            except (json.JSONDecodeError, TypeError):
                observation = {"raw": str(m.content)}
            steps.append(
                AgentStep(step=step_no, action=name, action_input=args, observation=observation)
            )
    return steps


def _final_answer(messages: list[Any]) -> str:
    for m in reversed(messages):
        if m.__class__.__name__ == "AIMessage" and not getattr(m, "tool_calls", None):
            return m.content if isinstance(m.content, str) else str(m.content)
    return ""


def run_langchain_agent(
    question: str,
    db: Session,
    model: Any = None,
    recursion_limit: int = 8,
) -> AgentResponse:
    from langchain.agents import create_agent

    from app.core.llm_clients import get_langchain_chat

    chat = model or get_langchain_chat()
    tools = build_tools(db)
    agent = create_agent(chat, tools, system_prompt=DEFAULT_SYSTEM_PROMPT)

    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": question}]},
            config={"recursion_limit": recursion_limit},
        )
    except Exception as exc:  # 연결/그래프 오류
        name = exc.__class__.__name__
        if "Recursion" in name:
            return AgentResponse(
                answer="최대 단계 수에 도달해 종료했습니다.", steps=[], stopped_by="max_steps"
            )
        if "Connection" in name or "APIConnection" in name:
            raise InfraError(
                "LLM 서버에 연결할 수 없습니다. 로컬 모델 서버 기동 여부를 확인하세요."
            ) from exc
        raise

    messages = result["messages"]
    return AgentResponse(
        answer=_final_answer(messages),
        steps=_extract_steps(messages),
        stopped_by="final_answer",
    )
