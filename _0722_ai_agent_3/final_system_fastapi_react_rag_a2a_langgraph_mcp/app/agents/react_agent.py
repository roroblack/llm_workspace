# -*- coding: utf-8 -*-
"""도구 선택·실행·관찰 루프를 수행하는 ReAct 고객 상담 에이전트입니다."""

from threading import Lock
from typing import Literal

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from app.agents.tools import ALL_TOOLS, current_provider
from app.services.llm_factory import create_chat_model

SYSTEM_PROMPT = """
너는 승승장구몰 통합 CS 상담원이다. 반드시 친절하고 정확한 한국어로 답한다.
주문 상태는 get_order_status, 재고는 get_stock, FAQ는 search_faq를 사용한다.
환불·교환·반품·멤버십 정책 질문은 policy_search가 반환한 PDF 근거로만 답한다.
고객이 실제 교환·환불·반품 처리를 요청하면 다른 설명을 붙이지 말고
'담당 부서로 연결해 드리겠습니다.'라고 정확히 답한다. 이 실행성 문의는 API 계층에서
customer_complaint 테이블에 먼저 저장된 뒤 에이전트 응답으로 전달된다.
도구 결과가 없거나 실패하면 값을 추측하거나 만들어 내지 않는다.
최종 답변에는 내부 사고 과정은 노출하지 않고 확인된 결과와 필요한 안내만 제공한다.
""".strip()

_agent_lock = Lock()
_agents: dict[str, object] = {}
_memory = InMemorySaver()


def get_react_agent(provider: Literal["openai", "gemini"]):
    """공급자별 ReAct 에이전트를 한 번 생성해 재사용합니다."""
    if provider in _agents:
        return _agents[provider]
    with _agent_lock:
        if provider not in _agents:
            _agents[provider] = create_agent(
                model=create_chat_model(provider),
                tools=ALL_TOOLS,
                system_prompt=SYSTEM_PROMPT,
                checkpointer=_memory,
            )
    return _agents[provider]


def invoke_react_agent(message: str, thread_id: str, provider: Literal["openai", "gemini"]) -> str:
    """동일 thread_id의 메모리를 유지하며 ReAct 에이전트를 실행합니다."""
    token = current_provider.set(provider)
    try:
        agent = get_react_agent(provider)
        result = agent.invoke(
            {"messages": [{"role": "user", "content": message}]},
            config={"configurable": {"thread_id": thread_id}},
        )
        return str(result["messages"][-1].content)
    finally:
        current_provider.reset(token)
