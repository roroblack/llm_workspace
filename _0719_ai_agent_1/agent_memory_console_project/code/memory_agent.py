# -*- coding: utf-8 -*-
"""LangGraph InMemorySaver를 사용하는 기억형 상담 에이전트 기능입니다."""

# create_agent는 LangChain의 에이전트를 간단히 생성합니다.
from langchain.agents import create_agent
# 메시지 클래스는 수동 기록, 트리밍, 요약 예제를 구성할 때 사용합니다.
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, trim_messages
# InMemorySaver는 thread_id별 대화 상태를 메모리에 저장합니다.
from langgraph.checkpoint.memory import InMemorySaver

# 제공된 common.py의 get_chat 함수로 OpenAI/Gemini 모델을 공통 생성합니다.
from code.common import get_chat
# 모델별 응답 형식 차이를 처리하는 공통 함수를 가져옵니다.
from code.message_utils import message_to_text

# 상담원 역할을 모든 메모리 에이전트에서 일관되게 사용합니다.
SYSTEM_PROMPT = "너는 승승장구몰의 친절한 CS 상담원이다. 제공된 정보만 근거로 한국어 존댓말로 답하라."


def build_agent(provider: str, temperature: float = 0.3):
    """선택한 모델과 InMemorySaver를 결합한 상담 에이전트를 생성합니다."""
    # common.py를 통해 선택한 공급자의 LangChain 채팅 모델을 생성합니다.
    llm = get_chat(provider=provider, temperature=temperature)
    # InMemorySaver를 생성하여 대화 상태를 thread_id별로 저장하게 합니다.
    checkpointer = InMemorySaver()
    # 도구 없이 대화 기억에 집중하는 에이전트를 생성합니다.
    return create_agent(
        llm,
        tools=[],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )


def chat(agent, text: str, thread_id: str):
    """같은 thread_id의 이전 대화를 자동 복원하여 한 번의 대화를 실행합니다."""
    # configurable 아래의 thread_id가 대화 세션을 구분하는 핵심 키입니다.
    config = {"configurable": {"thread_id": thread_id}}
    # 이번 호출에는 새로운 사용자 메시지만 전달하고 이전 기록은 checkpointer가 복원합니다.
    result = agent.invoke({"messages": [{"role": "user", "content": text}]}, config)
    # 마지막 메시지를 현재 턴의 모델 답변으로 선택합니다.
    final_message = result["messages"][-1]
    # 모델 종류와 관계없이 안전한 문자열로 변환합니다.
    answer = message_to_text(final_message)
    # 답변 문자열과 누적 메시지 목록을 함께 반환합니다.
    return answer, result["messages"]


def stateless_call(provider: str, user_text: str) -> str:
    """이전 기록을 전달하지 않는 독립적인 LLM 호출을 실행합니다."""
    # 매 호출마다 새 모델 객체를 생성합니다.
    llm = get_chat(provider=provider, temperature=0.3)
    # 현재 사용자 질문 하나만 전달하므로 이전 대화를 알 수 없습니다.
    response = llm.invoke(user_text)
    # 응답 객체를 안전한 문자열로 변환합니다.
    return message_to_text(response)


def manual_memory_turn(provider: str, history: list, user_text: str) -> str:
    """애플리케이션이 메시지 목록을 직접 누적하는 수동 메모리 방식을 실행합니다."""
    # 사용자 발화를 HumanMessage 객체로 변환하여 기록에 추가합니다.
    history.append(HumanMessage(content=user_text))
    # 선택한 공급자의 채팅 모델을 생성합니다.
    llm = get_chat(provider=provider, temperature=0.3)
    # 지금까지 누적한 전체 대화를 모델에 전달합니다.
    response = llm.invoke(history)
    # 모델 응답을 AIMessage 형태 그대로 기록에 추가합니다.
    history.append(response)
    # 화면 출력을 위해 응답을 문자열로 변환합니다.
    return message_to_text(response)


def trim_recent(messages: list, keep: int = 4) -> list:
    """시스템 메시지를 유지하면서 최근 메시지만 남깁니다."""
    # trim_messages는 메시지 경계를 보존하며 최근 항목을 선택합니다.
    return trim_messages(
        messages,
        max_tokens=keep,
        strategy="last",
        token_counter=len,
        include_system=True,
        start_on="human",
    )


def summarize_old(provider: str, messages: list, keep_recent: int = 4) -> list:
    """오래된 대화를 한 문장으로 요약하고 최근 메시지는 원문 그대로 보존합니다."""
    # 시스템 메시지만 별도로 분리합니다.
    system_messages = [message for message in messages if isinstance(message, SystemMessage)]
    # 일반 대화 메시지만 별도로 분리합니다.
    conversation = [message for message in messages if not isinstance(message, SystemMessage)]
    # 메시지 수가 기준 이하이면 요약할 필요가 없으므로 원본을 반환합니다.
    if len(conversation) <= keep_recent:
        return messages
    # 오래된 대화와 최근 대화를 기준 개수로 분리합니다.
    old_messages = conversation[:-keep_recent]
    # 최근 대화는 원문을 보존합니다.
    recent_messages = conversation[-keep_recent:]
    # 오래된 대화를 LLM이 이해할 수 있는 대화록 문자열로 변환합니다.
    transcript = "\n".join(
        f"{'사용자' if isinstance(message, HumanMessage) else '상담원'}: {message_to_text(message)}"
        for message in old_messages
    )
    # 요약은 일관성을 높이기 위해 temperature 0으로 실행합니다.
    llm = get_chat(provider=provider, temperature=0.0)
    # 개인정보와 중요한 조건을 유지하도록 명시적으로 요약을 요청합니다.
    summary_response = llm.invoke(
        "다음 상담 대화를 한국어 한 문장으로 요약하되, 고객 이름·주문번호·선호·요청 조건은 보존하라.\n\n"
        + transcript
    )
    # 모델 응답을 문자열로 안전하게 변환합니다.
    summary = message_to_text(summary_response)
    # 오래된 여러 메시지를 하나의 시스템 요약 메시지로 대체합니다.
    compressed_message = SystemMessage(content=f"[이전 대화 요약] {summary}")
    # 기존 시스템 지침, 압축 요약, 최근 대화 순서로 새 목록을 구성합니다.
    return system_messages + [compressed_message] + recent_messages


def build_demo_messages() -> list:
    """트리밍과 요약 결과를 비교하기 위한 긴 상담 대화 예시를 생성합니다."""
    # 시스템 역할과 여러 턴의 상담 대화를 메시지 객체 목록으로 구성합니다.
    return [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content="내 이름은 민준이야."),
        AIMessage(content="네, 민준님. 반갑습니다."),
        HumanMessage(content="주문번호는 ORD-1001이야."),
        AIMessage(content="주문번호 ORD-1001을 확인하겠습니다."),
        HumanMessage(content="배송이 늦고 있어."),
        AIMessage(content="배송 상태를 확인해 보겠습니다."),
        HumanMessage(content="전자기기를 좋아해."),
        AIMessage(content="전자기기 선호를 참고하겠습니다."),
        HumanMessage(content="환불 가능 여부도 알고 싶어."),
        AIMessage(content="환불 정책과 주문 상태를 함께 확인하겠습니다."),
        HumanMessage(content="지금까지 말한 내용을 기억해 줘."),
        AIMessage(content="네, 주요 내용을 기억하겠습니다."),
    ]
