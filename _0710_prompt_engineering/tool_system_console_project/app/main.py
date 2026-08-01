# -*- coding: utf-8 -*-
"""PyCharm에서 바로 실행하는 제6강 Tool System 콘솔 앱입니다."""

from __future__ import annotations

# sys는 프로그램 종료 처리에 사용합니다.
import sys

# torch_demo는 PyTorch 텐서 분석 예제를 실행합니다.
from torch_demo import run_torch_summary

# gemini_tools는 Gemini API 기반 도구 선택/실행 예제를 제공합니다.
from gemini_tools import (
    run_gemini_answer_demo,
    run_gemini_tool_choice_demo,
    run_similar_tool_demo,
)

# openai_tools는 OpenAI API 기반 도구 선택/실행 예제를 제공합니다.
from openai_tools import run_openai_tool_choice_demo, run_openai_tool_execution_demo


def print_menu() -> None:
    """콘솔 메뉴를 출력합니다."""
    # 메뉴 제목을 출력합니다.
    print("\n" + "=" * 80)
    print("제6강 Tool System 콘솔 실습 앱")
    print("=" * 80)
    # 각 실행 메뉴를 출력합니다.    
    print("1. PyTorch 상품/재고 텐서 분석")
    print("2. Gemini 도구 선택 관찰")
    print("3. Gemini 자동 도구 실행")
    print("4. Gemini 비슷한 도구 구분 실험")
    print("5. OpenAI 도구 선택 관찰")
    print("6. OpenAI 도구 실행 후 최종 답변")
    print("0. 종료")


def read_int(prompt: str, default: int | None = None) -> int | None:
    """사용자 입력을 정수로 변환하고 실패하면 기본값을 반환합니다."""
    # 사용자에게 입력을 받습니다.
    value = input(prompt).strip()
    # 아무 입력이 없고 기본값이 있으면 기본값을 반환합니다.
    if not value and default is not None:
        return default
    # 정수 변환을 시도합니다.
    try:
        return int(value)
    # 변환 실패 시 안내 후 기본값을 반환합니다.
    except ValueError:
        print("숫자를 입력해야 합니다.")
        return default


def main() -> None:
    """사용자 메뉴 입력에 따라 실습 기능을 실행합니다."""
    # 무한 반복으로 메뉴를 계속 보여 줍니다.
    while True:
        # 메뉴를 출력합니다.
        print_menu()
        # 메뉴 번호를 입력받습니다.
        choice = input("메뉴 선택: ").strip()
        # 0번은 프로그램 종료입니다.
        if choice == "0":
            print("프로그램을 종료합니다.")
            sys.exit(0)
        # 1번은 HTML 파일 목록 출력입니다.
        if  choice == "1":
            run_torch_summary()
        # 2번은 Gemini 도구 선택 관찰입니다.
        elif choice == "2":
            run_gemini_tool_choice_demo()
        # 3번은 Gemini 자동 도구 실행입니다.
        elif choice == "3":
            run_gemini_answer_demo()
        # 4번은 비슷한 도구 구분 실험입니다.
        elif choice == "4":
            run_similar_tool_demo()
        # 5번은 OpenAI 도구 선택 관찰입니다.
        elif choice == "5":
            run_openai_tool_choice_demo()
        # 6번은 OpenAI 도구 실행 후 최종 답변입니다.
        elif choice == "6":
            run_openai_tool_execution_demo()
        # 정의되지 않은 메뉴는 안내합니다.
        else:
            print("메뉴 번호를 다시 선택하세요.")


# 이 파일을 직접 실행할 때만 main 함수를 호출합니다.
if __name__ == "__main__":
    main()
