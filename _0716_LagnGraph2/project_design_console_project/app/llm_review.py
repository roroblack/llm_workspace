# -*- coding: utf-8 -*-
"""선택한 OpenAI 또는 Gemini로 설계안 검토를 실행합니다."""

# LangChain 메시지 객체를 가져옵니다.
from langchain_core.messages import SystemMessage, HumanMessage
# 원본 common.py의 get_chat 함수를 가져옵니다.
from app.common_bridge import get_chat
# 설계 명세 클래스를 가져옵니다.
from app.project_design import AgentSpec


def review_design(provider: str) -> str:
    """선택한 provider로 현재 설계의 과잉·누락·위험을 검토합니다."""
    # 현재 프로젝트의 기본 설계 명세를 생성합니다.
    spec = AgentSpec()
    # 선택한 provider에 맞는 LangChain ChatModel을 생성합니다.
    llm = get_chat(provider=provider, temperature=0.1)
    # LLM에 전달할 설계 요약 문자열을 구성합니다.
    design_text = (
        f"이름={spec.name}\n도구={spec.tools}\nRAG={spec.use_rag}\n"
        f"단기메모리={spec.use_memory}\n멀티에이전트={spec.use_multi_agent}\n"
        "진입점=answer(message, thread_id) -> str"
    )
    # 설계 검토 역할과 입력 설계를 메시지로 전달합니다.
    response = llm.invoke([
        SystemMessage("너는 AI 백엔드 아키텍처 검토자다. 설계의 누락, 과잉, 운영 위험을 각각 한 가지씩 한국어로 검토하라."),
        HumanMessage(design_text),
    ])
    # 모델 응답 본문을 문자열로 반환합니다.
    return str(response.content)
