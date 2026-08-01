# -*- coding: utf-8 -*-
"""OpenAI API와 LangChain OpenAI 모델을 사용하는 Planning Agent 실습 모듈입니다."""

# traceback은 API 오류를 콘솔에 확인하기 위해 사용합니다.
import traceback

# planning_core에는 공통 계획 생성·검증 로직이 들어 있습니다.
from planning_core import (
    Plan,
    make_fallback_plan,
    make_plan,
    print_plan,
    validate_plan,
    replan,
    list_tasks,
    recommend_next_task_without_llm,
)


# OpenAI provider 이름을 상수로 관리합니다.
PROVIDER = "openai"


def run_openai_planner() -> None:
    """OpenAI LangChain 모델로 목표를 하위 작업으로 분해합니다."""
    # 사용자에게 목표를 입력받습니다.
    goal = input("목표를 입력하세요: ").strip()

    # 빈 입력이면 기본 목표를 사용합니다.
    if not goal:
        goal = "승승장구몰 신상품 '가을 패딩' 출시"

    # API 호출 실패에 대비합니다.
    try:
        # OpenAI 모델로 구조화 출력 Plan을 생성합니다.
        plan = make_plan(PROVIDER, goal)
    except SystemExit as error:
        # common.py에서 API 키 오류가 발생하면 폴백을 사용합니다.
        print(error)
        print("API 키가 없어 규칙 기반 예시 계획으로 대체합니다.")
        plan = make_fallback_plan(goal)
    except Exception:
        # 기타 오류도 앱을 종료하지 않고 처리합니다.
        print("OpenAI 계획 생성 중 오류가 발생했습니다. 규칙 기반 예시 계획으로 대체합니다.")
        traceback.print_exc()
        plan = make_fallback_plan(goal)

    # 계획 결과를 출력합니다.
    print("\n[OpenAI Planner 결과]")
    print_plan(plan)


def run_openai_validation_replan() -> None:
    """나쁜 계획을 검증하고 OpenAI 모델로 재계획합니다."""
    # 실습 목표를 지정합니다.
    goal = "승승장구몰 신상품 '가을 패딩' 출시"

    # 일부러 부실한 계획을 생성합니다.
    bad_plan = Plan(goal=goal, steps=["그냥 출시한다"])

    # 계획 검증을 수행합니다.
    ok, reason = validate_plan(bad_plan)

    # 검증 결과를 출력합니다.
    print("\n[나쁜 계획 검증]")
    print_plan(bad_plan)
    print(f"검증 결과: {'적합' if ok else '부적합'} - {reason}")

    # 검증 실패 시 재계획합니다.
    if not ok:
        try:
            # 실패 사유를 피드백으로 넣어 OpenAI에게 재계획을 요청합니다.
            fixed_plan = replan(PROVIDER, goal, reason)
        except SystemExit as error:
            # 키가 없으면 규칙 기반 계획으로 대체합니다.
            print(error)
            print("API 키가 없어 규칙 기반 예시 계획으로 대체합니다.")
            fixed_plan = make_fallback_plan(goal)
        except Exception:
            # 오류를 출력하고 폴백 계획을 사용합니다.
            print("OpenAI 재계획 중 오류가 발생했습니다. 규칙 기반 예시 계획으로 대체합니다.")
            traceback.print_exc()
            fixed_plan = make_fallback_plan(goal)

        # 재계획 결과를 출력합니다.
        print("\n[재계획 결과]")
        print_plan(fixed_plan)


def run_openai_executor_demo() -> None:
    """OpenAI 호출 전에도 확인 가능한 실행 에이전트용 도구 결과를 출력합니다."""
    # list_tasks 도구 함수로 전체 작업을 조회합니다.
    print("\n[작업 목록 조회]")
    print(list_tasks("전체"))

    # 규칙 기반 추천 결과를 출력합니다.
    print("\n[다음 작업 추천]")
    print(recommend_next_task_without_llm())
