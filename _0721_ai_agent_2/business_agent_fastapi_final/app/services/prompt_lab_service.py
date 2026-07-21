# -*- coding: utf-8 -*-
"""Prompt Engineering 실습용 직접 LLM 호출 서비스입니다.

LangGraph 분류 경로를 거치지 않고, 사용자가 화면에서 지정한
System Prompt / 수행 지시문 / temperature / top_p / few-shot 을
그대로 반영해 결과가 어떻게 달라지는지 비교하기 위한 모듈입니다.
"""

# 시스템/사용자/모델 역할 메시지를 구성하기 위해 LangChain 메시지 클래스를 가져옵니다.
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
# 공급자별 채팅 모델 생성 함수를 가져옵니다.
from app.core.common import get_chat, GEMINI_MODEL
# 실제 적용된 모델명을 표시하기 위해 os 를 가져옵니다.
import os
# 응답 객체를 문자열로 변환하는 유틸리티를 가져옵니다.
from app.services.message_utils import extract_text

# few-shot 실험에서 사용할 비즈니스 도메인 예시(입력→모범 출력) 쌍입니다.
FEW_SHOT_EXAMPLES = [
    (
        "2026-03 매출이 전월 대비 어떻게 변했는지 한 줄로 요약해줘.",
        "2026-03 매출은 전월 대비 소폭 증가했습니다. 핵심 동인은 상위 카테고리의 판매 회복입니다.",
    ),
    (
        "재고가 부족한 상품을 어떻게 보고하면 좋을까?",
        "부족 상품명, 현재 재고량, 최근 판매 속도, 예상 소진일을 표 형태로 간결히 보고하세요.",
    ),
]


def _build_messages(system_prompt: str, instruction: str, message: str, few_shot: bool) -> list:
    """System → (few-shot) → Human 순서의 메시지 목록을 구성합니다."""
    # 최종적으로 모델에 전달할 메시지 목록을 준비합니다.
    messages: list = []
    # System Prompt 가 비어 있지 않으면 첫 번째 메시지로 추가합니다.
    if system_prompt.strip():
        messages.append(SystemMessage(content=system_prompt.strip()))
    # few-shot 이 켜져 있으면 예시 대화쌍을 실제 질문 앞에 넣습니다.
    if few_shot:
        for example_user, example_ai in FEW_SHOT_EXAMPLES:
            messages.append(HumanMessage(content=example_user))
            messages.append(AIMessage(content=example_ai))
    # 지시문이 있으면 질문 앞에 붙여 하나의 사용자 메시지로 만듭니다.
    if instruction.strip():
        human_text = f"{instruction.strip()}\n\n[질문]\n{message.strip()}"
    else:
        human_text = message.strip()
    # 실제 실험 질문을 마지막 사용자 메시지로 추가합니다.
    messages.append(HumanMessage(content=human_text))
    # 완성된 메시지 목록을 반환합니다.
    return messages


def run_prompt_lab(
    message: str,
    provider: str,
    prompt_type: str,
    system_prompt: str,
    instruction: str,
    temperature: float,
    top_p: float,
    few_shot: bool,
) -> dict[str, object]:
    """지정된 프롬프트 설정으로 LLM 을 직접 호출하고 결과와 적용 설정을 반환합니다."""
    # 선택한 공급자·temperature·top_p 로 채팅 모델을 생성합니다.
    llm = get_chat(provider=provider, temperature=temperature, top_p=top_p)
    # System/few-shot/Human 메시지를 구성합니다.
    messages = _build_messages(system_prompt, instruction, message, few_shot)
    # 모델을 호출하고 응답을 문자열로 변환합니다.
    answer = extract_text(llm.invoke(messages))
    # 실제 사용된 모델명을 공급자에 맞춰 계산합니다.
    model_name = GEMINI_MODEL if provider == "gemini" else os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    # 답변과 함께 이번 실행에 실제 적용된 설정을 echo 하여 비교를 돕습니다.
    return {
        "answer": answer,
        "settings": {
            "provider": provider,
            "model": model_name,
            "prompt_type": prompt_type,
            "temperature": temperature,
            "top_p": top_p,
            "few_shot": few_shot,
        },
    }
