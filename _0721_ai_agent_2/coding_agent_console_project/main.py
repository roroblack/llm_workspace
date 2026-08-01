# -*- coding: utf-8 -*-
"""PyCharm에서 바로 실행하는 제23강 Coding Agent 콘솔 앱의 시작 파일입니다."""

from __future__ import annotations

import sys
from pathlib import Path

# main.py에서 code/common.py와 기능 모듈을 가져올 수 있도록 code 폴더를 검색 경로에 추가합니다.
PROJECT_ROOT = Path(__file__).resolve().parent
CODE_DIR = PROJECT_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from common import DATA  # noqa: E402
from app_context import get_provider, set_provider  # noqa: E402
from coding_agent import (  # noqa: E402
    DEFAULT_FIXED,
    DEFAULT_TARGET,
    LOOP_FIXED,
    ask_fix,
    extract_code,
    fix_once,
    read_code,
    run_code,
    save_code,
    self_debug,
)
from data_tools import inspect_sales_csv, list_data_files  # noqa: E402
from exercises import exercise_custom_bug, exercise_summary  # noqa: E402


def print_title(title: str) -> None:
    """실행 결과 영역을 알아보기 쉽게 구분해 출력합니다."""
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def choose_provider() -> None:
    """사용자가 OpenAI와 Gemini 중 사용할 모델 공급자를 선택하게 합니다."""
    while True:
        print("\nLLM 공급자를 선택하세요.")
        print("1. OpenAI")
        print("2. Gemini")
        choice = input("선택: ").strip()
        if choice == "1":
            set_provider("openai")
            return
        if choice == "2":
            set_provider("gemini")
            return
        print("1 또는 2를 입력하세요.")


def menu_data_check() -> None:
    """data.zip에서 복사된 데이터 파일과 핵심 CSV 샘플을 확인합니다."""
    print_title("1. data.zip 데이터 파일 확인")
    files = list_data_files()
    for path in files:
        print("-", path.relative_to(DATA))
    print(f"\n총 {len(files)}개 파일")
    print("\n[sales_daily.csv 앞 5행]")
    for row in inspect_sales_csv():
        print(row)


def menu_original_error() -> None:
    """원본 buggy_script.py를 별도 프로세스로 실행해 실제 오류를 확인합니다."""
    print_title("2. 원본 버그 스크립트 실행")
    result = run_code(DEFAULT_TARGET)
    print(f"종료코드: {result.returncode}")
    print(result.combined_output)


def menu_read_and_request() -> None:
    """원본을 읽고 LLM에 수정 요청한 뒤 코드만 미리보기로 출력합니다."""
    print_title("3. 코드 읽기 → LLM 수정 요청 → 코드블록 추출")
    source = read_code(DEFAULT_TARGET)
    fixed = ask_fix(source, get_provider())
    # 이 메뉴는 저장·실행 전 단계 확인용이므로 파일을 바꾸지 않고 일부만 보여 줍니다.
    print(fixed[:3000])


def menu_fix_and_verify() -> None:
    """수정 코드를 새 파일로 저장하고 실제 실행해 종료코드로 검증합니다."""
    print_title("4. 새 파일 저장 → subprocess 격리 실행 → 검증")
    _code, result = fix_once(DEFAULT_TARGET, DEFAULT_FIXED, get_provider())
    print("원본:", DEFAULT_TARGET)
    print("수정본:", DEFAULT_FIXED)
    print(f"종료코드: {result.returncode} (0=정상)")
    print(result.combined_output)


def menu_self_debug() -> None:
    """실패 오류를 LLM에 다시 전달하는 self-debugging 루프를 실행합니다."""
    print_title("5. 재귀적 버그 수정 오류 피드백 루프")
    success, history, _latest = self_debug(
        DEFAULT_TARGET,
        LOOP_FIXED,
        get_provider(),
        max_tries=3,
    )
    for index, result in enumerate(history, start=1):
        print(f"\n[시도 {index}] 종료코드: {result.returncode}")
        print(result.combined_output)
    print("\n최종 결과:", "성공" if success else "실패 — 사람 검토 필요")
    print("수정본:", LOOP_FIXED)


def menu_extract_demo() -> None:
    """LLM 설명이 섞였을 때 정규식으로 코드만 추출하는 핵심 함수를 확인합니다."""
    print_title("6. 코드블록 추출 정규식 확인")
    sample = "설명 문장입니다.\n```python\nprint('코드만 추출')\n```\n추가 설명"
    print("[원본 응답]\n", sample)
    print("\n[추출 결과]\n", extract_code(sample))


def print_menu() -> None:
    """HTML 설명 메뉴를 제외하고 중요한 실행 코드 메뉴만 출력합니다."""
    print("\n" + "-" * 72)
    print(f"제23강 Coding Agent 콘솔 앱 | 현재 LLM: {get_provider().upper()}")
    print("-" * 72)
    print("1. data.zip 데이터 파일 및 sales_daily.csv 확인")
    print("2. 원본 buggy_script.py 실행 오류 확인")
    print("3. 코드 읽기·LLM 수정 요청·코드블록 추출")
    print("4. 수정본 새 파일 저장·격리 실행·종료코드 검증")
    print("5. 재귀적 버그 수정 오류 피드백 루프")
    print("6. 코드블록 추출 정규식 단독 확인")
    print("8-1. 실습문제 해답 1 — 변경 요약과 코드 분리")
    print("8-2. 실습문제 해답 2 — 새 버그 파일 self-debugging")
    print("9. OpenAI / Gemini 다시 선택")
    print("0. 종료")


def main() -> None:
    """공급자를 먼저 선택하고 사용자가 종료할 때까지 메뉴를 반복 실행합니다."""
    choose_provider()
    actions = {
        "1": menu_data_check,
        "2": menu_original_error,
        "3": menu_read_and_request,
        "4": menu_fix_and_verify,
        "5": menu_self_debug,
        "6": menu_extract_demo,
        "8-1": lambda: exercise_summary(get_provider()),
        "8-2": lambda: exercise_custom_bug(get_provider()),
        "9": choose_provider,
    }
    while True:
        print_menu()
        choice = input("메뉴 선택: ").strip()
        if choice == "0":
            print("프로그램을 종료합니다.")
            break
        action = actions.get(choice)
        if action is None:
            print("목록에 있는 메뉴 번호를 입력하세요.")
            continue
        try:
            action()
        except Exception as error:
            # 메뉴 하나의 오류가 콘솔 앱 전체 종료로 이어지지 않도록 최상위에서 처리합니다.
            print(f"\n[실행 오류] {type(error).__name__}: {error}")


if __name__ == "__main__":
    main()
