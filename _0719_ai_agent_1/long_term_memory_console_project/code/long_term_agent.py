# -*- coding: utf-8 -*-
"""OpenAI와 Gemini에서 공통으로 실행되는 단기·장기 기억 에이전트 모듈입니다."""

# create_agent는 LangChain 모델과 도구를 연결해 도구 호출형 에이전트를 생성합니다.
from langchain.agents import create_agent
# InMemorySaver는 현재 프로세스 안에서 thread_id별 단기 대화 기록을 저장합니다.
from langgraph.checkpoint.memory import InMemorySaver

# 제공된 common.py의 get_chat 함수로 OpenAI 또는 Gemini 모델을 선택 생성합니다.
from code.common import get_chat
# JSON 기반 장기 기억 도구를 가져옵니다.
from code.long_term_store import get_profile, update_profile
# SQLite 기반 장기 기억 도구를 가져옵니다.
from code.long_term_store import get_profile_sqlite, update_profile_sqlite

# 상담원의 역할과 도구 사용 규칙을 일관되게 적용할 시스템 프롬프트를 정의합니다.
SYSTEM_PROMPT = (
    "너는 승승장구몰의 친절한 고객 상담원이다. 반드시 한국어 존댓말로 답하라. "
    "고객이 이름, 선호, 관심사, 알레르기, 배송 선호 등 장기간 유지할 정보를 말하면서 기억하거나 저장해 달라고 하면 "
    "반드시 쓰기 도구를 호출하라. 추천이나 개인화 상담 전에는 반드시 읽기 도구로 고객 프로필을 확인하라. "
    "도구에 없는 정보는 추측하지 말고 없다고 명확하게 답하라."
)


def message_to_text(message) -> str:
    """OpenAI와 Gemini의 서로 다른 메시지 content 형식을 문자열로 통일합니다."""
    # LangChain 메시지에 text 속성이 있고 값이 문자열이면 가장 안전한 값을 바로 반환합니다.
    if hasattr(message, "text") and isinstance(message.text, str) and message.text:
        # 모델 공급자와 관계없이 문자열 답변을 반환합니다.
        return message.text
    # 일반적인 LangChain 메시지의 content 값을 가져옵니다.
    content = getattr(message, "content", message)
    # content가 문자열이면 그대로 반환합니다.
    if isinstance(content, str):
        # 문자열 답변을 호출자에게 반환합니다.
        return content
    # Gemini처럼 content blocks 목록이 반환된 경우 각 블록의 텍스트를 모읍니다.
    if isinstance(content, list):
        # 추출된 텍스트 조각을 저장할 빈 리스트를 생성합니다.
        text_parts: list[str] = []
        # content 블록을 하나씩 순회합니다.
        for block in content:
            # 딕셔너리 블록의 text 키가 문자열인지 확인합니다.
            if isinstance(block, dict) and isinstance(block.get("text"), str):
                # text 값을 결과 목록에 추가합니다.
                text_parts.append(block["text"])
            # 객체 블록에 text 속성이 있는지 확인합니다.
            elif hasattr(block, "text") and isinstance(block.text, str):
                # 객체의 text 값을 결과 목록에 추가합니다.
                text_parts.append(block.text)
        # 추출된 모든 문자열을 줄바꿈으로 연결하여 반환합니다.
        return "\n".join(text_parts).strip()
    # 예상하지 못한 형식은 문자열 표현으로 변환하여 프로그램 중단을 방지합니다.
    return str(content)


def build_long_term_agent(provider: str, backend: str = "json", temperature: float = 0.0):
    """선택한 LLM과 JSON 또는 SQLite 장기 기억 도구를 결합합니다."""
    # common.py를 통해 선택된 공급자의 LangChain 채팅 모델을 생성합니다.
    llm = get_chat(provider=provider, temperature=temperature)
    # JSON 백엔드를 선택했는지 확인합니다.
    if backend == "json":
        # JSON 읽기·쓰기 도구 목록을 구성합니다.
        tools = [get_profile, update_profile]
    # SQLite 백엔드를 선택했는지 확인합니다.
    elif backend == "sqlite":
        # SQLite 읽기·쓰기 도구 목록을 구성합니다.
        tools = [get_profile_sqlite, update_profile_sqlite]
    # 지원하지 않는 저장소 이름은 명확한 오류로 처리합니다.
    else:
        # 허용 값과 함께 ValueError를 발생시킵니다.
        raise ValueError("backend는 'json' 또는 'sqlite'만 사용할 수 있습니다.")
    # 장기 기억 도구와 단기 기억 체크포인터를 함께 사용하는 에이전트를 생성합니다.
    return create_agent(
        llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=InMemorySaver(),
    )


def say(agent, text: str, thread_id: str) -> tuple[str, list]:
    """지정한 thread_id로 한 턴을 실행하고 최종 답변과 누적 메시지를 반환합니다."""
    # configurable 아래 thread_id를 넣어 단기 대화 세션을 구분합니다.
    config = {"configurable": {"thread_id": thread_id}}
    # 새 사용자 메시지 하나를 전달하며 과거 메시지는 InMemorySaver가 자동 복원합니다.
    result = agent.invoke({"messages": [{"role": "user", "content": text}]}, config)
    # 결과 목록의 마지막 메시지를 현재 턴의 최종 모델 답변으로 선택합니다.
    final_message = result["messages"][-1]
    # 모델별 메시지 형식 차이를 제거하여 문자열 답변을 만듭니다.
    answer = message_to_text(final_message)
    # 답변 문자열과 전체 누적 메시지 목록을 반환합니다.
    return answer, result["messages"]
