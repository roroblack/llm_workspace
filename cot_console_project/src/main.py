# -*- coding: utf-8 -*-
"""
main.py

실행 방법:
    python src/main.py

프로젝트 목적:
    - 제공된 common.py를 공통 모듈로 사용합니다.
    - Python + Torch + Gemini API + OpenAI API 실습을 메뉴 방식으로 실행합니다.
"""

# traceback은 예외 발생 시 상세 원인을 확인하고 싶을 때 사용할 수 있습니다.
import traceback

# common.py를 직접 실행하지 않고도 경로와 키 상태를 확인하기 위해 필요한 값을 가져옵니다.
from common import DATA, DOCS, GEMINI_MODEL, ROOT

# llm_clients 모듈에서 Gemini/OpenAI 호출 함수를 가져옵니다.
from llm_clients import (
    ask_gemini_cot,
    ask_gemini_direct,
    ask_openai_cot,
    ask_openai_direct,
    verify_gemini,
    verify_openai,
)

# torch_metrics 모듈에서 API 없는 정답률 계산 데모 함수를 가져옵니다.
from torch_metrics import run_offline_accuracy_demo


# 실습에 공통으로 사용할 예제 문제입니다.
SAMPLE_QUESTION = "이어버드를 79000원에 3개 샀는데 10% 쿠폰을 받았습니다. 총 결제액은?"


def print_project_info() -> None:
    """프로젝트 경로와 데이터 폴더 상태를 출력합니다."""
    # 프로젝트 루트 경로를 출력합니다.
    print("\n[프로젝트 정보]")
    print("-" * 80)
    print(f"ROOT         : {ROOT}")
    print(f"DATA         : {DATA} / 존재={DATA.exists()}")
    print(f"DOCS         : {DOCS} / 존재={DOCS.exists()}")
    print(f"GEMINI_MODEL : {GEMINI_MODEL}")


def run_gemini_demo() -> None:
    """Gemini API로 직접 답변, CoT 답변, 자기검증을 실행합니다."""
    # 실습 문제를 출력합니다.
    print("\n[Gemini API 실습]")
    print("-" * 80)
    print(f"문제: {SAMPLE_QUESTION}")

    # 직접 답변을 요청합니다.
    direct = ask_gemini_direct(SAMPLE_QUESTION)

    # CoT 답변을 요청합니다.
    cot = ask_gemini_cot(SAMPLE_QUESTION)

    # CoT 답변을 검산합니다.
    verified = verify_gemini(SAMPLE_QUESTION, cot)

    # 직접 답변 결과를 출력합니다.
    print("\n[직접 답변]")
    print(direct)

    # CoT 답변 결과를 출력합니다.
    print("\n[CoT 답변]")
    print(cot)

    # 검산 결과를 출력합니다.
    print("\n[자기검증 결과]")
    print(verified)


def run_openai_demo() -> None:
    """OpenAI API로 직접 답변, CoT 답변, 자기검증을 실행합니다."""
    # 실습 문제를 출력합니다.
    print("\n[OpenAI API 실습]")
    print("-" * 80)
    print(f"문제: {SAMPLE_QUESTION}")

    # 직접 답변을 요청합니다.
    direct = ask_openai_direct(SAMPLE_QUESTION)

    # CoT 답변을 요청합니다.
    cot = ask_openai_cot(SAMPLE_QUESTION)

    # CoT 답변을 검산합니다.
    verified = verify_openai(SAMPLE_QUESTION, cot)

    # 직접 답변 결과를 출력합니다.
    print("\n[직접 답변]")
    print(direct)

    # CoT 답변 결과를 출력합니다.
    print("\n[CoT 답변]")
    print(cot)

    # 검산 결과를 출력합니다.
    print("\n[자기검증 결과]")
    print(verified)


def print_menu() -> None:
    """콘솔 메뉴를 출력합니다."""
    # 메뉴 제목을 출력합니다.
    print("\n" + "=" * 80)
    print("CoT Reasoning Prompt 콘솔 실습 앱")
    print("=" * 80)

    # 메뉴 항목을 출력합니다.
    print("1. 프로젝트/공통 모듈 정보 확인")  
    print("2. Torch 기반 정답률 비교 실행(API 키 불필요)")
    print("3. Gemini API 직접 답변 + CoT + 자기검증 실행")
    print("4. OpenAI API 직접 답변 + CoT + 자기검증 실행")
    print("0. 종료")


def main() -> None:
    """사용자 입력에 따라 각 실습 기능을 실행하는 메인 루프입니다."""
    # 프로그램이 종료될 때까지 메뉴를 반복해서 보여 줍니다.
    while True:
        # 메뉴를 출력합니다.
        print_menu()

        # 사용자 선택값을 입력받습니다.
        choice = input("\n메뉴 번호를 입력하세요: ").strip()

        # 사용자가 0을 입력하면 반복문을 종료합니다.
        if choice == "0":
            print("프로그램을 종료합니다.")
            break

        # 각 메뉴 실행 중 오류가 나더라도 전체 프로그램이 종료되지 않도록 try로 감쌉니다.
        try:
            # 1번 메뉴는 프로젝트 정보를 출력합니다.
            if choice == "1":
                print_project_info()           

            # 2번 메뉴는 Torch 정확도 데모를 실행합니다.
            elif choice == "2":
                run_offline_accuracy_demo()

            # 3번 메뉴는 Gemini API 실습을 실행합니다.
            elif choice == "3":
                run_gemini_demo()

            # 4번 메뉴는 OpenAI API 실습을 실행합니다.
            elif choice == "4":
                run_openai_demo()

            # 정의되지 않은 번호는 안내합니다.
            else:
                print("[안내] 메뉴에 있는 번호를 입력하세요.")

        # common.py의 require_key는 API 키가 없으면 SystemExit을 발생시키므로 별도로 처리합니다.
        except SystemExit as exc:
            print(exc)

        # 그 밖의 모든 예외를 잡아 오류 원인을 출력합니다.
        except Exception as exc:
            print(f"[실행 오류] {exc}")
            print("상세 오류:")
            traceback.print_exc()


# 이 파일을 직접 실행했을 때만 main()을 호출합니다.
if __name__ == "__main__":
    main()
