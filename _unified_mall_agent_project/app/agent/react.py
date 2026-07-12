"""수동 ReAct 루프 (원리 학습용).

Thought → Action(도구) → Observation 반복. 안전장치: max_steps, 중복 호출 차단,
history trimming. chat_fn을 주입할 수 있어 모델 없이 결정론적으로 테스트한다.

오류 경계 (Codex 합의):
- 비즈니스 실패는 도구가 {"ok": false}로 반환 → 관찰로 모델에 전달(멈추지 않음).
- 인프라 실패(LLM 서버 다운, DB 오류, 설정)는 삼키지 않고 예외로 전파.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from app.agent.schemas import AgentResponse, AgentStep
from app.core.errors import InfraError
from app.core.llm_clients import get_active_model, get_chat_client
from app.tools.commerce_tools import TOOL_MAP, TOOLS_SCHEMA

DEFAULT_SYSTEM_PROMPT = (
    "너는 승승장구몰의 상담 에이전트다. 필요하면 도구를 호출해 가격·재고·주문상태·"
    "환율을 확인하고, 정책·매뉴얼은 지식 문서 검색(search_knowledge_base)으로 확인한 뒤 "
    "답한다. 재고가 재주문 기준 이하이면 재주문이 필요하다고 판단한다. "
    "최종 답변은 한국어로 간결하게 작성한다."
)

# chat_fn(messages, tools) -> assistant message dict
# assistant dict: {"role":"assistant","content":str|None,"tool_calls":list|None}
ChatFn = Callable[[list[dict], list[dict]], dict]


def _default_chat_fn(messages: list[dict], tools: list[dict]) -> dict:
    """실제 LLM 호출 (OpenAI 호환). 연결 실패는 InfraError로 올린다."""
    from openai import APIConnectionError

    client = get_chat_client()
    model = get_active_model()
    try:
        resp = client.chat.completions.create(
            model=model, messages=messages, tools=tools, temperature=0
        )
    except APIConnectionError as exc:
        raise InfraError(
            "LLM 서버에 연결할 수 없습니다. 로컬 모델 서버(scripts/local_model_server.py) "
            "기동 여부를 확인하세요."
        ) from exc
    m = resp.choices[0].message
    tool_calls = None
    if m.tool_calls:
        tool_calls = [
            {"id": tc.id, "name": tc.function.name, "arguments": tc.function.arguments}
            for tc in m.tool_calls
        ]
    return {"role": "assistant", "content": m.content, "tool_calls": tool_calls}


def _assistant_to_openai(assistant: dict) -> dict:
    """내부 assistant dict → OpenAI 메시지 형식."""
    msg: dict[str, Any] = {"role": "assistant", "content": assistant.get("content") or ""}
    if assistant.get("tool_calls"):
        msg["tool_calls"] = [
            {
                "id": tc["id"],
                "type": "function",
                "function": {"name": tc["name"], "arguments": tc["arguments"]},
            }
            for tc in assistant["tool_calls"]
        ]
    return msg


def _tool_message(tool_call_id: str, observation: dict) -> dict:
    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": json.dumps(observation, ensure_ascii=False),
    }


def _trim(messages: list[dict], keep: int = 8) -> list[dict]:
    """head(system+user 2개) + 최근 keep개. tail이 tool로 시작하면 짝을 안 깨게 보정."""
    if len(messages) <= keep + 2:
        return messages
    head = messages[:2]
    tail = messages[-keep:]
    # tail이 tool 메시지로 시작하면 앞의 assistant를 잃은 것 → 하나 더 포함
    while tail and tail[0].get("role") == "tool":
        tail = messages[-(len(tail) + 1):]
        if len(tail) >= len(messages) - 2:
            break
    return head + tail


def _signature(name: str, args: dict) -> str:
    return f"{name}:{json.dumps(args, sort_keys=True, ensure_ascii=False)}"


def run_react_agent(
    question: str,
    db: Session,
    chat_fn: ChatFn | None = None,
    max_steps: int = 3,
    system_prompt: str | None = None,
) -> AgentResponse:
    chat_fn = chat_fn or _default_chat_fn
    messages: list[dict] = [
        {"role": "system", "content": system_prompt or DEFAULT_SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    steps: list[AgentStep] = []
    seen: set[str] = set()

    for step_no in range(1, max_steps + 1):
        messages = _trim(messages)
        assistant = chat_fn(messages, TOOLS_SCHEMA)
        # assistant 메시지를 tool 결과보다 먼저 append (OpenAI 순서)
        messages.append(_assistant_to_openai(assistant))

        tool_calls = assistant.get("tool_calls")
        if not tool_calls:
            return AgentResponse(
                answer=assistant.get("content") or "",
                steps=steps,
                stopped_by="final_answer",
            )

        for tc in tool_calls:
            name = tc["name"]
            raw_args = tc.get("arguments")
            # 인자 JSON 파싱 (실패는 비즈니스 관찰로 반환, 인프라 아님)
            try:
                args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
            except json.JSONDecodeError:
                observation = {
                    "ok": False,
                    "error_code": "bad_arguments",
                    "message": f"도구 인자 JSON 파싱 실패: {raw_args!r}",
                }
                messages.append(_tool_message(tc["id"], observation))
                steps.append(
                    AgentStep(step=step_no, action=name, action_input={}, observation=observation)
                )
                continue

            sig = _signature(name, args)
            if sig in seen:
                return AgentResponse(
                    answer="동일한 도구와 인자가 반복 호출되어 무한루프 방지 장치가 작동했습니다.",
                    steps=steps,
                    stopped_by="duplicate_tool_call",
                )
            seen.add(sig)

            fn = TOOL_MAP.get(name)
            if fn is None:
                observation = {
                    "ok": False,
                    "error_code": "unknown_tool",
                    "message": f"알 수 없는 도구: {name}",
                }
            else:
                # 인자 개수/이름 불일치(TypeError)는 잘못된 입력 → 구조화 관찰.
                # 그 외 예외(InfraError 등)는 삼키지 않고 전파 (Codex 합의).
                try:
                    observation = fn(db, **args)
                except TypeError as exc:
                    observation = {
                        "ok": False,
                        "error_code": "bad_arguments",
                        "message": f"도구 인자 오류: {exc}",
                    }

            messages.append(_tool_message(tc["id"], observation))
            steps.append(
                AgentStep(step=step_no, action=name, action_input=args, observation=observation)
            )

    return AgentResponse(
        answer="최대 단계 수에 도달해 종료했습니다.", steps=steps, stopped_by="max_steps"
    )
