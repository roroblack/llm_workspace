# -*- coding: utf-8 -*-
"""PyCharm에서 바로 실행하는 Planning Agent 콘솔 앱의 시작 파일입니다."""

# torch_demo는 PyTorch 텐서로 프로젝트 상태를 집계하는 실습 모듈입니다.
from torch_demo import run_torch_status_demo

# gemini_app은 Gemini 기반 Planner와 재계획 실습 메뉴를 제공합니다.
from gemini_app import (
    run_gemini_executor_demo,
    run_gemini_plan_with_validation,
    run_gemini_planner,
    run_gemini_validation_replan,
)

# openai_app은 OpenAI 기반 Planner와 재계획 실습 메뉴를 제공합니다.
from openai_app import (
    run_openai_executor_demo,
    run_openai_planner,
    run_openai_validation_replan,
)


# 메뉴 번호와 실행 함수를 딕셔너리로 연결합니다.
MENU_ACTIONS = {
    "1": run_torch_status_demo,
    "2": run_gemini_planner,
    "3": run_gemini_validation_replan,
    "4": run_gemini_plan_with_validation,
    "5": run_gemini_executor_demo,
    "6": run_openai_planner,
    "7": run_openai_validation_replan,
    "8": run_openai_executor_demo,
}


def print_menu() -> None:
    """콘솔 메뉴를 출력합니다."""
    # 화면 구분을 위한 빈 줄과 제목을 출력합니다.
    print("\n" + "=" * 80)
    print("LangChain Planning Agent 콘솔 실습 앱")
    print("=" * 80)

    # PyTorch 실습 메뉴를 출력합니다.
    print("1. PyTorch 프로젝트 작업 상태 집계")

    # Gemini 실습 메뉴를 출력합니다.
    print("2. Gemini Planner 실행")
    print("3. Gemini 계획 검증 및 재계획")
    print("4. Gemini 계획 생성 → 검증 → 재계획 파이프라인")
    print("5. Gemini Executor용 작업 조회 데모")

    # OpenAI 실습 메뉴를 출력합니다.
    print("6. OpenAI Planner 실행")
    print("7. OpenAI 계획 검증 및 재계획")
    print("8. OpenAI Executor용 작업 조회 데모")

    # 종료 메뉴를 출력합니다.
    print("0. 종료")


def main() -> None:
    """사용자 입력을 받아 선택한 실습 메뉴를 실행합니다."""
    # 사용자가 종료를 선택할 때까지 반복합니다.
    while True:
        # 메뉴를 출력합니다.
        print_menu()

        # 사용자에게 메뉴 번호를 입력받습니다.
        choice = input("메뉴 번호를 선택하세요: ").strip()

        # 0을 입력하면 반복문을 종료합니다.
        if choice == "0":
            print("프로그램을 종료합니다.")
            break

        # 선택한 번호에 해당하는 실행 함수를 가져옵니다.
        action = MENU_ACTIONS.get(choice)

        # 잘못된 번호를 입력하면 안내 후 다시 메뉴를 보여 줍니다.
        if action is None:
            print("잘못된 메뉴 번호입니다. 다시 선택하세요.")
            continue

        # 선택한 메뉴 실행 중 오류가 나도 전체 앱이 종료되지 않도록 처리합니다.
        try:
            action()
        except KeyboardInterrupt:
            # Ctrl+C 입력 시 현재 메뉴를 중단하고 메인 메뉴로 돌아갑니다.
            print("\n현재 작업을 중단했습니다.")
        except Exception as error:
            # 예상하지 못한 오류를 사용자에게 알려 줍니다.
            print(f"실행 중 오류가 발생했습니다: {error}")


# 이 파일을 직접 실행할 때만 main 함수를 호출합니다.
if __name__ == "__main__":
    main()
