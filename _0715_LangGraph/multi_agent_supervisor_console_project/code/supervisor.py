# -*- coding: utf-8 -*-
"""Supervisor가 질문을 전문 에이전트에 위임하는 중앙 제어 모듈입니다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# 역할별 전문 에이전트와 결과 객체를 가져옵니다.
from agents import AgentResult, SpecialistAgent, build_specialists
# 세 가지 라우터와 결과 객체를 가져옵니다.
from router import RouteDecision, build_router_llm, route_hybrid, route_llm, route_rule

# 메뉴에서 허용할 라우터 방식의 타입을 명시합니다.
RouterMode = Literal["rule", "llm", "hybrid"]


@dataclass(frozen=True)
class SupervisorResult:
    """Supervisor 판단과 전문 에이전트 결과를 하나로 묶는 실행 결과입니다."""

    question: str
    route: RouteDecision
    agent_result: AgentResult


class Supervisor:
    """중앙에서 질문을 분류하고 한 명의 전문 에이전트에게 위임합니다."""

    def __init__(self, provider: str) -> None:
        # 라우팅에 사용할 LLM을 생성합니다.
        self.router_llm = build_router_llm(provider)

        # 같은 공급자를 사용하는 추천·정책 전문 에이전트를 생성합니다.
        sales_agent, policy_agent = build_specialists(provider)

        # 라우팅 결과 문자열로 전문 에이전트를 바로 찾을 수 있도록 딕셔너리를 구성합니다.
        self.agents: dict[str, SpecialistAgent] = {
            "sales": sales_agent,
            "policy": policy_agent,
        }

    def decide(self, question: str, mode: RouterMode) -> RouteDecision:
        """선택한 모드에 따라 라우팅 결정을 생성합니다."""
        # 규칙 모드에서는 키워드 라우터를 실행합니다.
        if mode == "rule":
            decision = route_rule(question)

            # 순수 규칙 라우터가 애매함을 반환하면 HTML 예제의 기본 동작처럼 sales로 보냅니다.
            if decision.target == "unknown":
                return RouteDecision(
                    target="sales",
                    method="rule-default",
                    reason=f"{decision.reason}; 기본 대상 sales 적용",
                    llm_calls=0,
                )

            # 명확한 규칙 결과는 그대로 반환합니다.
            return decision

        # LLM 모드에서는 모든 질문을 LLM으로 분류합니다.
        if mode == "llm":
            return route_llm(self.router_llm, question)

        # 하이브리드 모드에서는 규칙 우선, 애매할 때만 LLM을 사용합니다.
        if mode == "hybrid":
            return route_hybrid(self.router_llm, question)

        # 허용하지 않은 문자열이 들어오면 즉시 오류를 발생시킵니다.
        raise ValueError(f"지원하지 않는 라우터 모드입니다: {mode}")

    def run(self, question: str, mode: RouterMode = "hybrid") -> SupervisorResult:
        """라우팅 결정을 내리고 선택된 전문 에이전트에 질문을 위임합니다."""
        # 빈 질문은 LLM 호출 전에 차단합니다.
        if not question.strip():
            raise ValueError("질문이 비어 있습니다. 내용을 입력해 주세요.")

        # 선택한 라우팅 방식으로 담당 전문 에이전트를 결정합니다.
        decision = self.decide(question, mode)

        # 결정된 대상 이름으로 전문 에이전트 객체를 가져옵니다.
        agent = self.agents[decision.target]

        # 원래 사용자 질문을 변경하지 않고 전문 에이전트에 전달합니다.
        agent_result = agent.run(question)

        # 중앙 라우팅 정보와 전문 에이전트 실행 결과를 함께 반환합니다.
        return SupervisorResult(
            question=question,
            route=decision,
            agent_result=agent_result,
        )
