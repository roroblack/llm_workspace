"""Plan-and-Execute Planning (PDF5).

목표를 하위 단계로 분해(Pydantic Plan 구조화 출력) → 검증 → 실패 시 재계획 루프.

에러 정책 (Codex 합의):
- goal 빈값(사용자 입력 오류) → ValidationErr(422)
- LLM Plan 단계 검증 실패 → 내부 재계획(예외 아님)
- max_replan 초과 후에도 실패 → LLMOutputError(502)
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field

from app.core.errors import LLMOutputError, ValidationErr

MIN_STEPS = 2
MAX_STEPS = 8


class Plan(BaseModel):
    goal: str = Field(description="달성할 목표")
    steps: list[str] = Field(description="목표를 이루기 위한 순차 단계")


def validate_plan(plan: Plan) -> list[str]:
    """계획의 문제점 목록을 반환한다 (빈 리스트 = 유효). 예외를 던지지 않는다."""
    problems: list[str] = []
    n = len(plan.steps)
    if n < MIN_STEPS:
        problems.append(f"단계가 너무 적습니다({n} < {MIN_STEPS}).")
    if n > MAX_STEPS:
        problems.append(f"단계가 너무 많습니다({n} > {MAX_STEPS}).")
    if any(not (s and s.strip()) for s in plan.steps):
        problems.append("빈 단계가 있습니다.")
    return problems


def make_plan(goal: str, model: Any = None) -> Plan:
    """LangChain with_structured_output(Plan)으로 계획 생성 (LLM).

    로컬 Gemma는 tool-calling 미지원이라 라이브는 실키에서만. 테스트는 make 주입.
    """
    if not goal or not goal.strip():
        raise ValidationErr("goal이 비어 있습니다.")
    from app.core.llm_clients import get_langchain_chat

    chat = model or get_langchain_chat()
    structured = chat.with_structured_output(Plan)
    return structured.invoke(
        f"다음 목표를 {MIN_STEPS}~{MAX_STEPS}개의 실행 단계로 분해하라. 목표: {goal}"
    )


def replan(goal: str, reason: str, model: Any = None) -> Plan:
    """실패 사유를 피드백해 다시 계획을 생성한다 (LLM)."""
    from app.core.llm_clients import get_langchain_chat

    chat = model or get_langchain_chat()
    structured = chat.with_structured_output(Plan)
    return structured.invoke(
        f"이전 계획이 다음 이유로 부적합했다: {reason}. "
        f"{MIN_STEPS}~{MAX_STEPS}개 단계로 다시 분해하라. 목표: {goal}"
    )


def plan_with_validation(
    goal: str,
    make: Callable[[str], Plan] | None = None,
    remake: Callable[[str, str], Plan] | None = None,
    max_replan: int = 2,
) -> Plan:
    """생성→검증→(실패 시)재계획 루프. make/remake 주입 가능(테스트).

    max_replan 초과 후에도 검증 실패면 LLMOutputError.
    """
    if not goal or not goal.strip():
        raise ValidationErr("goal이 비어 있습니다.")
    make = make or (lambda g: make_plan(g))
    remake = remake or (lambda g, r: replan(g, r))

    def _attempt(fn) -> tuple[Plan | None, list[str]]:
        # 구조화 출력 파싱/스키마 예외도 '문제'로 흡수해 재계획 대상으로 삼는다.
        # (조용히 삼키는 폴백이 아니라, 재시도 후 최종 실패 시 LLMOutputError로 노출)
        try:
            plan = fn()
        except Exception as exc:  # noqa: BLE001 - LLM 출력 오류 전반
            return None, [f"구조화 출력 오류: {exc}"]
        return plan, validate_plan(plan)

    plan, problems = _attempt(lambda: make(goal))
    attempts = 0
    while problems and attempts < max_replan:
        attempts += 1
        reason = "; ".join(problems)
        plan, problems = _attempt(lambda: remake(goal, reason))

    if problems:
        raise LLMOutputError(f"유효한 계획 생성 실패(재계획 {attempts}회): {problems}")
    return plan
