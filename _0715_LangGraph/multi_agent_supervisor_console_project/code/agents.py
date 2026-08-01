# -*- coding: utf-8 -*-
"""추천 및 정책 역할을 분리한 전문 에이전트 모듈입니다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

# 제공된 common.py의 get_chat 함수를 사용하여 공급자별 LLM을 생성합니다.
from common import get_chat
# CSV 데이터를 검색하는 Python 도구 함수를 가져옵니다.
from data_repository import search_faq, search_products
# 여러 형태의 LLM 응답을 문자열로 바꾸는 공통 함수를 가져옵니다.
from message_utils import extract_text


@dataclass(frozen=True)
class AgentResult:
    """전문 에이전트 실행 결과와 사용 근거를 함께 보관하는 데이터 객체입니다."""

    agent_name: str
    tool_name: str
    tool_input: str
    evidence: str
    answer: str


class SpecialistAgent:
    """역할별 프롬프트와 전용 도구 하나를 가진 간단하고 명시적인 전문 에이전트입니다."""

    def __init__(
        self,
        *,
        name: str,
        role_prompt: str,
        tool_name: str,
        tool_function: Callable[[str], str],
        provider: str,
    ) -> None:
        # 에이전트 이름을 인스턴스 변수에 저장합니다.
        self.name = name
        # 해당 에이전트가 지켜야 할 역할 지시문을 저장합니다.
        self.role_prompt = role_prompt
        # 실행할 전용 도구 이름을 저장합니다.
        self.tool_name = tool_name
        # 실제 CSV 검색을 수행하는 Python 함수를 저장합니다.
        self.tool_function = tool_function
        # common.py의 get_chat을 사용해 선택된 공급자의 채팅 모델을 생성합니다.
        self.llm = get_chat(provider=provider, temperature=0.0)

    def _extract_tool_input(self, question: str) -> str:
        """LLM을 사용해 사용자 질문에서 도구에 전달할 짧은 검색어를 추출합니다."""
        # 도구마다 적합한 입력을 한 줄로 추출하도록 제한적인 프롬프트를 구성합니다.
        prompt = (
            f"역할: {self.role_prompt}\n"
            f"사용 도구: {self.tool_name}\n"
            "다음 고객 질문에서 도구 검색에 사용할 가장 핵심적인 한국어 검색어만 출력하라. "
            "설명, 따옴표, 문장부호 없이 한 단어나 짧은 구만 출력한다.\n"
            f"고객 질문: {question}\n"
            "검색어:"
        )

        # 선택된 LLM에 검색어 추출 프롬프트를 전달합니다.
        response = self.llm.invoke(prompt)

        # 모델 응답 객체에서 실제 텍스트를 안전하게 추출합니다.
        keyword = extract_text(response).strip(" \"'`.,")

        # 모델이 빈 문자열을 반환하면 원래 질문을 검색어로 사용해 실행을 계속합니다.
        return keyword or question

    def _compose_answer(self, question: str, evidence: str) -> str:
        """도구가 찾은 근거만 사용하여 최종 고객 답변을 생성합니다."""
        # 모델이 근거 밖 내용을 만들지 않도록 역할과 근거 제한을 명시합니다.
        prompt = (
            f"당신은 {self.role_prompt}\n"
            "아래 도구 실행 결과만 근거로 사용하여 고객에게 한국어로 답하라. "
            "근거에 없는 내용을 추측하지 말고, 핵심 답변 뒤에 '[근거: 내부 CSV]'를 표시하라.\n\n"
            f"고객 질문:\n{question}\n\n"
            f"도구 실행 결과:\n{evidence}\n\n"
            "최종 답변:"
        )

        # LLM에 최종 답변 생성을 요청합니다.
        response = self.llm.invoke(prompt)

        # 모델 반환 객체에서 텍스트를 추출하여 반환합니다.
        return extract_text(response)

    def run(self, question: str) -> AgentResult:
        """검색어 추출 → 전용 도구 실행 → 근거 기반 답변 생성 순서로 처리합니다."""
        # 빈 질문은 외부 API를 호출하기 전에 즉시 거부하여 불필요한 비용을 방지합니다.
        if not question.strip():
            raise ValueError("질문이 비어 있습니다. 내용을 입력해 주세요.")

        # LLM으로 전용 도구에 전달할 핵심 검색어를 추출합니다.
        tool_input = self._extract_tool_input(question)

        # 이 에이전트에 허용된 전용 Python 도구만 실행합니다.
        evidence = self.tool_function(tool_input)

        # 도구가 반환한 근거를 바탕으로 최종 자연어 답변을 생성합니다.
        answer = self._compose_answer(question, evidence)

        # 실행 추적에 필요한 모든 정보를 AgentResult로 묶어 반환합니다.
        return AgentResult(
            agent_name=self.name,
            tool_name=self.tool_name,
            tool_input=tool_input,
            evidence=evidence,
            answer=answer,
        )


def build_specialists(provider: str) -> tuple[SpecialistAgent, SpecialistAgent]:
    """동일한 LLM 공급자를 사용하되 역할과 도구가 다른 두 전문 에이전트를 생성합니다."""
    # 상품 추천 업무만 담당하는 sales 전문 에이전트를 생성합니다.
    sales_agent = SpecialistAgent(
        name="sales",
        role_prompt=(
            "승승장구몰의 상품 추천 전문 상담원이다. 상품의 카테고리, 가격, 평점, 재고를 "
            "근거로 추천하고 정책 질문에는 답하지 않는다."
        ),
        tool_name="search_products",
        tool_function=search_products,
        provider=provider,
    )

    # 환불·배송·교환 등 정책 업무만 담당하는 policy 전문 에이전트를 생성합니다.
    policy_agent = SpecialistAgent(
        name="policy",
        role_prompt=(
            "승승장구몰의 정책 및 FAQ 전문 상담원이다. 환불, 교환, 배송, 취소, 적립 정책을 "
            "FAQ 근거로만 안내하고 상품 추천은 하지 않는다."
        ),
        tool_name="search_faq",
        tool_function=search_faq,
        provider=provider,
    )

    # Supervisor가 선택해 사용할 수 있도록 두 에이전트를 튜플로 반환합니다.
    return sales_agent, policy_agent
