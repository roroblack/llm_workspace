# -*- coding: utf-8 -*-
"""Gemini API와 LangChain Gemini 모델을 사용하는 Planning Agent 실습 모듈입니다."""

# traceback은 오류 발생 시 개발자가 원인을 확인하기 쉽게 출력하기 위해 사용합니다.
import traceback

# planning_core에는 Plan 생성, 검증, 재계획, 작업 조회 로직이 들어 있습니다.
from planning_core import (
    Plan,
    make_fallback_plan,
    make_plan,
    plan_with_validation,
    print_plan,
    validate_plan,
    replan,
    list_tasks,
    recommend_next_task_without_llm,
)


# Gemini provider 이름을 상수로 관리하여 오타를 줄입니다.
PROVIDER = "gemini"


def run_gemini_planner() -> None:
    """Gemini LangChain 모델로 목표를 하위 작업으로 분해합니다."""
    # 사용자에게 목표 입력을 받습니다.
    goal = input("목표를 입력하세요: ").strip()

    # 빈 입력이면 기본 예제를 사용합니다.
    if not goal:
        goal = "승승장구몰 신상품 '가을 패딩' 출시"

    # API 키가 없거나 호출에 실패해도 콘솔 앱이 종료되지 않도록 예외를 처리합니다.
    try:
        # Gemini 모델로 구조화 출력 Plan을 생성합니다.
        plan = make_plan(PROVIDER, goal)
    except SystemExit as error:
        # common.py의 require_key가 SystemExit을 발생시키면 안내 후 폴백 계획을 사용합니다.
        print(error)
        print("API 키가 없어 규칙 기반 예시 계획으로 대체합니다.")
        plan = make_fallback_plan(goal)
    except Exception:
        # 그 외 API 오류도 앱이 멈추지 않도록 처리합니다.
        print("Gemini 계획 생성 중 오류가 발생했습니다. 규칙 기반 예시 계획으로 대체합니다.")
        traceback.print_exc()
        plan = make_fallback_plan(goal)

    # 최종 계획을 출력합니다.
    print("\n[Gemini Planner 결과]")
    print_plan(plan)


def run_gemini_validation_replan() -> None:
    """나쁜 계획을 검증하고 Gemini로 재계획하는 흐름을 확인합니다."""
    # 실습용 목표를 지정합니다.
    goal = "승승장구몰 신상품 '가을 패딩' 출시"

    # 일부러 단계가 1개뿐인 나쁜 계획을 만듭니다.
    bad_plan = Plan(goal=goal, steps=["그냥 출시한다"])

    # 나쁜 계획을 검증합니다.
    ok, reason = validate_plan(bad_plan)

    # 검증 결과를 출력합니다.
    print("\n[나쁜 계획 검증]")
    print_plan(bad_plan)
    print(f"검증 결과: {'적합' if ok else '부적합'} - {reason}")

    # 검증에 실패하면 재계획을 요청합니다.
    if not ok:
        try:
            # 실패 사유를 피드백으로 넣어 Gemini에게 재계획을 요청합니다.
            fixed_plan = replan(PROVIDER, goal, reason)
        except SystemExit as error:
            # API 키가 없으면 폴백 계획을 사용합니다.
            print(error)
            print("API 키가 없어 규칙 기반 예시 계획으로 대체합니다.")
            fixed_plan = make_fallback_plan(goal)
        except Exception:
            # 기타 오류가 발생해도 앱이 중단되지 않도록 합니다.
            print("Gemini 재계획 중 오류가 발생했습니다. 규칙 기반 예시 계획으로 대체합니다.")
            traceback.print_exc()
            fixed_plan = make_fallback_plan(goal)

        # 재계획 결과를 출력합니다.
        print("\n[재계획 결과]")
        print_plan(fixed_plan)


def run_gemini_plan_with_validation() -> None:
    """계획 생성 → 검증 → 필요 시 재계획 전체 파이프라인을 실행합니다."""
    # 사용자에게 목표를 입력받습니다.
    goal = input("목표를 입력하세요: ").strip()

    # 입력이 없으면 기본 목표를 사용합니다.
    if not goal:
        goal = "승승장구몰 신상품 '가을 패딩' 출시"

    # 전체 파이프라인을 예외 처리로 감쌉니다.
    try:
        # Gemini 기반 계획 검증 파이프라인을 실행합니다.
        plan = plan_with_validation(PROVIDER, goal)
    except SystemExit as error:
        # 키가 없으면 폴백 계획으로 대체합니다.
        print(error)
        print("API 키가 없어 규칙 기반 예시 계획으로 대체합니다.")
        plan = make_fallback_plan(goal)
    except Exception:
        # 기타 오류도 안전하게 처리합니다.
        print("Gemini 계획 검증 파이프라인 중 오류가 발생했습니다. 규칙 기반 예시 계획으로 대체합니다.")
        traceback.print_exc()
        plan = make_fallback_plan(goal)

    # 최종 채택 계획을 출력합니다.
    print("\n[최종 채택 계획]")
    print_plan(plan)


def run_gemini_executor_demo() -> None:
    """LangChain create_agent 없이도 진행상황 조회 결과를 콘솔에서 확인합니다."""
    # 전체 작업 목록을 도구 함수로 조회합니다.
    all_tasks = list_tasks("전체")

    # 대기 작업 중 우선순위가 높은 작업을 규칙 기반으로 추천합니다.
    next_task = recommend_next_task_without_llm()

    # 결과를 출력합니다.
    print("\n[작업 목록 조회]")
    print(all_tasks)
    print("\n[다음 작업 추천]")
    print(next_task)
