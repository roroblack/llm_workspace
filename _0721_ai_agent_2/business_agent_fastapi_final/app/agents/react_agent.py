# -*- coding: utf-8 -*-
"""복합 질문을 도구 호출 반복으로 해결하는 ReAct 에이전트입니다."""

# 에이전트 실행 결과를 일반 문자열로 변환하기 위한 유틸리티를 가져옵니다.
from app.services.message_utils import extract_text
# 공급자별 채팅 모델을 생성하는 공통 함수를 가져옵니다.
from app.core.common import get_chat
# ReAct에서 사용할 도구 목록을 가져옵니다.
from app.agents.tools import build_tools

# 비즈니스 에이전트가 지켜야 할 핵심 규칙을 시스템 프롬프트로 정의합니다.
SYSTEM_PROMPT = """너는 근거 중심 비즈니스 분석 ReAct 에이전트다.
질문을 해결하기 전에 필요한 도구를 선택하고, 도구 결과를 관찰한 뒤 답하라.
CSV의 수치를 임의로 변경하거나 계산 결과를 창작하지 마라.
정책과 매뉴얼 질문은 반드시 internal_knowledge_search를 사용하라.
답변에는 사용한 데이터와 근거를 간결하게 명시하라."""


def run_react(message: str, provider: str, thread_id: str) -> str:
    """LangChain create_agent를 사용해 ReAct 도구 호출 루프를 실행합니다."""
    # LangChain의 최신 표준 에이전트 생성 함수를 지연 import합니다.
    from langchain.agents import create_agent
    # 멀티턴 상태 저장을 위한 LangGraph 메모리 체크포인터를 가져옵니다.
    from langgraph.checkpoint.memory import InMemorySaver
    # 선택한 공급자의 낮은 temperature 채팅 모델을 생성합니다.
    model = get_chat(provider=provider, temperature=0.1)
    # 도구와 시스템 프롬프트 및 메모리를 결합한 ReAct 에이전트를 생성합니다.
    agent = create_agent(model=model, tools=build_tools(), system_prompt=SYSTEM_PROMPT, checkpointer=InMemorySaver())
    # 사용자 메시지와 thread_id를 전달해 에이전트를 실행합니다.
    result = agent.invoke({"messages": [{"role": "user", "content": message}]}, config={"configurable": {"thread_id": thread_id}})
    # 최종 메시지 목록에서 마지막 답변을 추출합니다.
    messages = result.get("messages", [])
    # 메시지가 존재하면 마지막 응답을 문자열로 변환해 반환합니다.
    if messages:
        return extract_text(messages[-1])
    # 예상하지 못한 빈 결과는 명확한 기본 메시지로 처리합니다.
    return "ReAct 에이전트가 답변을 생성하지 못했습니다."
