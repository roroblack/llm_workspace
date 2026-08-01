# -*- coding: utf-8 -*-
"""규칙, LLM, 하이브리드 Supervisor 라우터를 구현한 모듈입니다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# 제공된 common.py에서 채팅 모델 생성 함수를 가져옵니다.
from common import get_chat
# LLM 응답의 content를 안전하게 문자열로 변환하는 함수를 가져옵니다.
from message_utils import extract_text

# 명시적인 정책 질문을 빠르게 찾기 위한 키워드 튜플입니다.
POLICY_WORDS: tuple[str, ...] = (
    "환불",
    "교환",
    "배송",
    "취소",
    "적립",
    "포인트",
    "무료배송",
    "회원",
    "등급",
    "반품",
)

# 명시적인 상품 추천 질문을 찾기 위한 키워드 튜플입니다.
SALES_WORDS: tuple[str, ...] = (
    "추천",
    "상품",
    "제품",
    "가성비",
    "인기",
    "선물",
    "전자기기",
    "패션",
    "식품",
)


@dataclass(frozen=True)
class RouteDecision:
    """라우팅 대상과 판단 방식 및 설명을 함께 전달하는 데이터 객체입니다."""

    target: str
    method: str
    reason: str
    llm_calls: int


def route_rule(question: str) -> RouteDecision:
    """키워드만 사용하여 빠르고 비용 없이 policy 또는 sales로 분류합니다."""
    # 입력 질문의 앞뒤 공백을 제거합니다.
    normalized = question.strip()

    # 정책 키워드가 하나라도 포함되어 있는지 검사합니다.
    policy_hits = [word for word in POLICY_WORDS if word in normalized]

    # 정책 키워드가 있으면 정책 에이전트로 즉시 라우팅합니다.
    if policy_hits:
        return RouteDecision(
            target="policy",
            method="rule",
            reason=f"정책 키워드 감지: {', '.join(policy_hits)}",
            llm_calls=0,
        )

    # 추천 키워드가 하나라도 포함되어 있는지 검사합니다.
    sales_hits = [word for word in SALES_WORDS if word in normalized]

    # 추천 키워드가 있으면 추천 에이전트로 즉시 라우팅합니다.
    if sales_hits:
        return RouteDecision(
            target="sales",
            method="rule",
            reason=f"추천 키워드 감지: {', '.join(sales_hits)}",
            llm_calls=0,
        )

    # 어느 쪽도 명확하지 않으면 애매함을 나타내는 unknown을 반환합니다.
    return RouteDecision(
        target="unknown",
        method="rule",
        reason="명시적인 정책 또는 추천 키워드를 찾지 못함",
        llm_calls=0,
    )


def route_llm(llm: Any, question: str) -> RouteDecision:
    """LLM의 의미 이해를 사용하여 질문을 policy 또는 sales로 분류합니다."""
    # 출력 형식을 두 라벨로 제한하는 분류 프롬프트를 구성합니다.
    prompt = (
        "고객 질문을 다음 두 라벨 중 하나로 분류하라.\n"
        "- policy: 환불, 취소, 반품, 교환, 배송 기간, 적립, 회원 정책 문의\n"
        "- sales: 상품 선택, 추천, 가격대, 카테고리, 인기 상품 문의\n"
        "반드시 policy 또는 sales 한 단어만 출력한다.\n"
        f"질문: {question}\n"
        "라벨:"
    )

    # 분류 전용 LLM을 한 번 호출합니다.
    response = llm.invoke(prompt)

    # 응답을 소문자 문자열로 변환합니다.
    answer = extract_text(response).lower()

    # policy 문자열이 포함되면 정책 에이전트를 선택합니다.
    if "policy" in answer:
        target = "policy"
    # 그 외에는 안전한 두 번째 라벨인 sales로 정규화합니다.
    else:
        target = "sales"

    # 호출 횟수 1회와 원본 분류 응답을 설명에 포함해 반환합니다.
    return RouteDecision(
        target=target,
        method="llm",
        reason=f"LLM 분류 응답: {answer!r}",
        llm_calls=1,
    )


def route_hybrid(llm: Any, question: str) -> RouteDecision:
    """명확한 질문은 규칙으로, 애매한 질문만 LLM으로 처리합니다."""
    # 먼저 비용이 없는 규칙 라우터를 실행합니다.
    rule_decision = route_rule(question)

    # 규칙이 policy 또는 sales를 명확히 결정했으면 그 결과를 그대로 반환합니다.
    if rule_decision.target != "unknown":
        return RouteDecision(
            target=rule_decision.target,
            method="hybrid-rule",
            reason=rule_decision.reason,
            llm_calls=0,
        )

    # 규칙으로 판단할 수 없는 애매한 질문에 대해서만 LLM 라우터를 호출합니다.
    llm_decision = route_llm(llm, question)

    # 하이브리드 경로를 명확히 표시한 결과를 반환합니다.
    return RouteDecision(
        target=llm_decision.target,
        method="hybrid-llm",
        reason=f"규칙 판단 불가 → {llm_decision.reason}",
        llm_calls=llm_decision.llm_calls,
    )


def build_router_llm(provider: str) -> Any:
    """Supervisor 분류에 사용할 temperature 0 채팅 모델을 생성합니다."""
    # common.py의 get_chat을 통해 Gemini 또는 OpenAI 모델을 동일한 인터페이스로 생성합니다.
    return get_chat(provider=provider, temperature=0.0)
