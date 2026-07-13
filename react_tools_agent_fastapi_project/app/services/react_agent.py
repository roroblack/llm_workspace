# -*- coding: utf-8 -*-
"""
OpenAI + LangChain Tools 기반 ReAct 에이전트 서비스입니다.

이 모듈은 LangChain의 tool 객체와 OpenAI ChatModel의 tool calling 기능을 이용해
다음 루프를 직접 구현합니다.

  1) 사용자 질문을 history에 넣습니다.
  2) LLM이 사용할 도구를 결정합니다.
  3) 파이썬 코드가 도구를 실제 실행합니다.
  4) 실행 결과를 ToolMessage로 다시 history에 넣습니다.
  5) 모델이 최종 답을 낼 때까지 반복합니다.

안전장치:
  - max_steps로 최대 반복 횟수를 제한합니다.
  - 같은 도구와 같은 인자의 중복 호출을 차단합니다.
"""

# json은 tool args를 안정적인 문자열로 직렬화하기 위해 사용합니다.
import json

# typing.Any는 도구 인자 dict 타입을 표현하기 위해 사용합니다.
from typing import Any

# LangChain 메시지 객체들을 가져옵니다.
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

# 공통 설정과 키 확인 함수를 가져옵니다.
from common import get_chat, has_key

# API 응답 스키마를 가져옵니다.
from app.schemas import AgentResponse, AgentStep

# 도구 목록과 이름 매핑을 가져옵니다.
from app.services.tools_service import TOOLS, TOOL_MAP


def _tool_signature(name: str, args: dict[str, Any]) -> str:
    """중복 호출 방지를 위해 도구명과 인자를 하나의 문자열 서명으로 만듭니다."""
    # dict의 키 순서가 달라도 같은 인자는 같은 문자열이 되도록 sort_keys=True를 사용합니다.
    return f"{name}:{json.dumps(args, ensure_ascii=False, sort_keys=True)}"


def _trim_messages(messages: list, keep: int = 8) -> list:
    """대화 기록이 너무 길어지는 것을 막기 위해 최근 메시지만 남깁니다."""
    # 메시지가 보존 기준 이하이면 그대로 반환합니다.
    if len(messages) <= keep + 2:
        return messages

    # 첫 번째 SystemMessage는 에이전트 규칙이므로 보존합니다.
    head = messages[:2]

    # 최근 keep개 메시지만 꼬리로 남깁니다.
    tail = messages[-keep:]

    # 앞부분과 최근 기록을 합쳐 반환합니다.
    return head + tail


def run_openai_react_agent(question: str, max_steps: int = 6) -> AgentResponse:
    """OpenAI 모델과 LangChain Tools로 ReAct 에이전트를 실행합니다."""
    # OpenAI API 키가 없으면 로컬 실행 안내 응답을 반환합니다.
    if not has_key("OPENAI_API_KEY"):
        return AgentResponse(
            answer=(
                "OPENAI_API_KEY가 설정되어 있지 않아 OpenAI ReAct 루프를 실행하지 않았습니다. "
                ".env 파일에 OPENAI_API_KEY를 설정한 뒤 다시 실행하세요. "
                "키가 없어도 /api/torch/stock-summary 와 /api/vector/search 는 로컬로 확인할 수 있습니다."
            ),
            steps=[],
            stopped_by="missing_openai_key",
        )

    # LangChain OpenAI ChatModel을 생성합니다.
    llm = get_chat(provider="openai", temperature=0)

    # 모델에 도구 목록을 바인딩합니다.
    model_with_tools = llm.bind_tools(TOOLS)

    # 시스템 메시지는 ReAct 에이전트의 역할과 규칙을 정의합니다.
    system_message = SystemMessage(
        content=(
            "너는 승승장구몰의 ReAct 에이전트다. "
            "필요하면 도구를 호출해 가격, 재고, 주문상태, 강의 지식을 확인한다. "
            "도구 결과를 관찰한 뒤 다음 행동을 결정한다. "
            "재고가 재주문 기준 이하이면 재주문 필요라고 판단한다. "
            "최종 답변은 한국어로 간결하게 작성한다."
        )
    )

    # 사용자 질문을 HumanMessage로 생성합니다.
    user_message = HumanMessage(content=question)

    # 대화 기록은 시스템 메시지와 사용자 질문으로 시작합니다.
    messages = [system_message, user_message]

    # 실행 단계 기록을 저장할 리스트입니다.
    steps: list[AgentStep] = []

    # 이미 실행한 도구 호출을 저장하는 set입니다.
    seen_calls: set[str] = set()

    # max_steps 횟수만큼 ReAct 루프를 반복합니다.
    for step_no in range(1, max_steps + 1):
        # 메시지가 길어지면 토큰 관리를 위해 trimming합니다.
        messages = _trim_messages(messages)

        # 현재 대화 기록을 모델에 전달하여 다음 행동을 결정하게 합니다.
        ai_message = model_with_tools.invoke(messages)

        # 모델 응답을 history에 추가합니다.
        messages.append(ai_message)

        # tool_calls가 없으면 모델이 최종 답을 낸 것으로 판단합니다.
        if not getattr(ai_message, "tool_calls", None):
            return AgentResponse(answer=ai_message.content, steps=steps, stopped_by="final_answer")

        # 모델이 요청한 도구 호출들을 순서대로 실행합니다.
        for tool_call in ai_message.tool_calls:
            # 도구 이름을 읽습니다.
            tool_name = tool_call["name"]

            # 도구 인자를 읽습니다.
            tool_args = tool_call.get("args", {})

            # 중복 호출 감지를 위한 서명을 만듭니다.
            signature = _tool_signature(tool_name, tool_args)

            # 같은 도구와 같은 인자를 이미 실행했다면 루프를 중단합니다.
            if signature in seen_calls:
                return AgentResponse(
                    answer="동일한 도구와 인자가 반복 호출되어 무한루프 방지 장치가 작동했습니다.",
                    steps=steps,
                    stopped_by="duplicate_tool_call",
                )

            # 처음 보는 호출이면 실행 기록에 저장합니다.
            seen_calls.add(signature)

            # 도구 이름이 등록되어 있지 않으면 오류 관찰을 만듭니다.
            if tool_name not in TOOL_MAP:
                observation = f"등록되지 않은 도구입니다: {tool_name}"
            else:
                # LangChain Tool 객체를 실제 실행합니다.
                observation = TOOL_MAP[tool_name].invoke(tool_args)

            # 단계 기록을 응답용 리스트에 추가합니다.
            steps.append(
                AgentStep(
                    step=step_no,
                    thought="모델이 질문과 관찰 결과를 바탕으로 도구 호출을 결정했습니다.",
                    action=tool_name,
                    action_input=tool_args,
                    observation=str(observation),
                )
            )

            # 도구 실행 결과를 ToolMessage로 만들어 모델에게 되돌려줍니다.
            messages.append(
                ToolMessage(
                    content=str(observation),
                    tool_call_id=tool_call["id"],
                )
            )

    # max_steps를 모두 사용하면 안전장치에 의해 종료합니다.
    return AgentResponse(
        answer="최대 반복 횟수에 도달하여 ReAct 루프를 중단했습니다.",
        steps=steps,
        stopped_by="max_steps",
    )
