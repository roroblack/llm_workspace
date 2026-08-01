# -*- coding: utf-8 -*-
"""PyCharm에서 실행하는 Function Calling 콘솔 앱의 시작 파일입니다."""

# tools 모듈은 모델 없이 직접 실행할 도구 함수와 Torch 통계 기능을 제공합니다.
from tools import test_tools_without_llm, torch_inventory_summary

# Gemini Function Calling 예제 함수를 가져옵니다.
from gemini_app import gemini_auto_function_calling, gemini_error_handling_demo, gemini_manual_function_calling

# OpenAI Tool Calling 예제 함수를 가져옵니다.
from openai_app import openai_manual_tool_calling


def print_menu() -> None:
    """콘솔 앱의 메뉴를 출력합니다."""
    # 메뉴 제목을 출력합니다.
    print("\n" + "=" * 70)
    print("제5강 Function Calling 콘솔 실습 앱")
    print("=" * 70)
    # API 없이 도구 함수만 직접 실행하는 메뉴입니다.
    print("1. 모델 없이 도구 함수 직접 테스트")
    # PyTorch 텐서로 재고 통계를 계산하는 메뉴입니다.
    print("2. Torch 재고 통계 계산")
    # Gemini 자동 Function Calling 메뉴입니다.
    print("3. Gemini 자동 Function Calling 실행")
    # Gemini 수동 루프 메뉴입니다.
    print("4. Gemini 수동 루프 실행")
    # Gemini 오류 처리 메뉴입니다.
    print("5. Gemini 도구 오류 처리 실행")
    # OpenAI Tool Calling 메뉴입니다.
    print("6. OpenAI Tool Calling 실행")
    # 종료 메뉴입니다.
    print("0. 종료")


def safe_run(func) -> None:
    """메뉴 함수 실행 중 발생한 오류를 잡아 콘솔 앱이 종료되지 않게 합니다."""
    # API 키 누락, 패키지 누락, 네트워크 오류 등을 모두 잡기 위해 넓게 예외 처리합니다.
    try:
        # 전달받은 메뉴 함수를 실행합니다.
        func()
    # SystemExit은 common.py의 require_key에서 API 키 누락 시 발생할 수 있습니다.
    except SystemExit as e:
        print(e)
    # ImportError는 패키지가 설치되지 않았을 때 발생할 수 있습니다.
    except ImportError as e:
        print(f"[패키지 설치 필요] {e}")
        print("터미널에서 pip install -r requirements.txt 를 실행하세요.")
    # 그 외 오류도 안내하고 프로그램은 계속 실행합니다.
    except Exception as e:
        print(f"[실행 오류] {e}")


def main() -> None:
    """사용자 입력에 따라 각 실습 메뉴를 실행합니다."""
    # 사용자가 종료를 선택할 때까지 반복합니다.
    while True:
        # 메뉴를 출력합니다.
        print_menu()
        # 사용자 선택값을 입력받습니다.
        choice = input("메뉴 번호를 입력하세요: ").strip()
        # 1번 메뉴는 HTML 파일 목록을 출력합니다.
        if choice == "1":            
            safe_run(test_tools_without_llm)
        # 4번 메뉴는 Torch 텐서 기반 재고 통계를 출력합니다.
        elif choice == "2":
            safe_run(torch_inventory_summary)
        # 5번 메뉴는 Gemini 자동 Function Calling을 실행합니다.
        elif choice == "3":
            safe_run(gemini_auto_function_calling)
        # 6번 메뉴는 Gemini 수동 Function Calling 루프를 실행합니다.
        elif choice == "4":
            safe_run(gemini_manual_function_calling)
        # 7번 메뉴는 도구 오류 처리 실습을 실행합니다.
        elif choice == "5":
            safe_run(gemini_error_handling_demo)
        # 8번 메뉴는 OpenAI Tool Calling 수동 루프를 실행합니다.
        elif choice == "6":
            safe_run(openai_manual_tool_calling)
        # 0번 메뉴는 프로그램을 종료합니다.
        elif choice == "0":
            print("프로그램을 종료합니다.")
            break
        # 정의되지 않은 번호를 입력하면 안내합니다.
        else:
            print("메뉴에 있는 번호를 입력하세요.")


# 이 파일을 직접 실행했을 때만 main 함수를 호출합니다.
if __name__ == "__main__":
    main()
