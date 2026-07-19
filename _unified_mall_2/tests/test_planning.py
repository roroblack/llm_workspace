"""Planning 검증·재계획 루프 테스트 (결정론, make 주입)."""

import pytest

from app.agent.planning import Plan, plan_with_validation, validate_plan
from app.core.errors import LLMOutputError, ValidationErr


def test_validate_plan_ok():
    assert validate_plan(Plan(goal="g", steps=["a", "b", "c"])) == []


def test_validate_plan_too_few():
    problems = validate_plan(Plan(goal="g", steps=["a"]))
    assert any("적" in p for p in problems)


def test_validate_plan_too_many():
    problems = validate_plan(Plan(goal="g", steps=[str(i) for i in range(9)]))
    assert any("많" in p for p in problems)


def test_validate_plan_empty_step():
    problems = validate_plan(Plan(goal="g", steps=["a", "  "]))
    assert any("빈" in p for p in problems)


def test_plan_with_validation_empty_goal():
    with pytest.raises(ValidationErr):
        plan_with_validation("  ")


def test_plan_with_validation_replan_recovers():
    calls = {"make": 0, "remake": 0}

    def make(goal):
        calls["make"] += 1
        return Plan(goal=goal, steps=["only one"])  # 처음엔 단계 부족

    def remake(goal, reason):
        calls["remake"] += 1
        return Plan(goal=goal, steps=["a", "b", "c"])  # 재계획은 유효

    plan = plan_with_validation("주문 취소 처리", make=make, remake=remake, max_replan=2)
    assert len(plan.steps) == 3
    assert calls["make"] == 1
    assert calls["remake"] == 1


def test_plan_with_validation_exhausts_to_llm_output_error():
    def make(goal):
        return Plan(goal=goal, steps=["one"])

    def remake(goal, reason):
        return Plan(goal=goal, steps=["one"])  # 계속 부적합

    with pytest.raises(LLMOutputError):
        plan_with_validation("목표", make=make, remake=remake, max_replan=2)


def test_plan_with_validation_recovers_from_malformed_output():
    """make가 구조화 출력 예외를 던져도 재계획으로 복구."""

    def make(goal):
        raise ValueError("스키마 파싱 실패(모의)")

    def remake(goal, reason):
        return Plan(goal=goal, steps=["a", "b"])

    plan = plan_with_validation("목표", make=make, remake=remake, max_replan=2)
    assert len(plan.steps) == 2


def test_plan_with_validation_malformed_exhausts():
    def make(goal):
        raise ValueError("파싱 실패")

    def remake(goal, reason):
        raise ValueError("또 파싱 실패")

    with pytest.raises(LLMOutputError):
        plan_with_validation("목표", make=make, remake=remake, max_replan=1)
