# -*- coding: utf-8 -*-
"""
main.py

PyCharm에서 실행하는 콘솔 진입 파일입니다.
이 파일은 사용자가 메뉴를 선택하면 각 실습 모듈의 함수를 호출합니다.
"""

# pathlib은 운영체제와 무관하게 파일 경로를 다루기 위해 사용합니다.
from pathlib import Path

# sys는 현재 프로젝트의 code 폴더를 import 경로에 추가하기 위해 사용합니다.
import sys

# PROJECT_ROOT는 현재 main.py가 들어 있는 프로젝트 루트 경로입니다.
PROJECT_ROOT = Path(__file__).resolve().parent

# CODE_DIR은 공통 모듈과 실습 모듈이 들어 있는 code 폴더 경로입니다.
CODE_DIR = PROJECT_ROOT / "code"

# code 폴더를 import 경로에 추가하여 from html_reader import ... 형식으로 불러올 수 있게 합니다.
sys.path.append(str(CODE_DIR))

# Torch 기반 재고 분석 기능을 가져옵니다.
from torch_inventory import run_torch_inventory_demo

# API 없이 동작하는 로컬 에이전트 루프 기능을 가져옵니다.
from local_agent_loop import run_local_agent_demo

# Gemini API 기반 Agent Loop 기능을 가져옵니다.
from gemini_agent_loop import run_gemini_agent_demo

# OpenAI API 기반 Agent Loop 기능을 가져옵니다.
from openai_agent_loop import run_openai_agent_demo

# 공통 모듈 상태 확인 함수를 가져오기 위해 common 모듈 전체를 가져옵니다.
import common


def print_title(title: str) -> None:
    """콘솔 화면에서 메뉴 제목을 보기 좋게 출력합니다."""
    # 구분선을 출력하여 이전 출력과 현재 출력이 섞이지 않게 합니다.
    print("\n" + "=" * 80)
    # 사용자가 선택한 기능 제목을 출력합니다.
    print(title)
    # 다시 구분선을 출력합니다.
    print("=" * 80)


def show_common_status() -> None:
    """common.py가 계산한 프로젝트 경로와 환경변수 로드 상태를 출력합니다."""
    # 공통 모듈이 인식한 프로젝트 루트 경로를 출력합니다.
    print("ROOT:", common.ROOT)
    # 공통 모듈이 인식한 data 폴더 경로를 출력합니다.
    print("DATA:", common.DATA, "/ exists:", common.DATA.exists())
    # 공통 모듈이 인식한 docs 폴더 경로를 출력합니다.
    print("DOCS:", common.DOCS, "/ exists:", common.DOCS.exists())
    # Gemini 모델 환경변수 값을 출력합니다.
    print("GEMINI_MODEL:", common.GEMINI_MODEL)
    # Google API 키가 실제로 채워졌는지 검사합니다.
    print("GOOGLE_API_KEY loaded:", bool(common.os.getenv("GOOGLE_API_KEY")))
    # OpenAI API 키가 실제로 채워졌는지 검사합니다.
    print("OPENAI_API_KEY loaded:", bool(common.os.getenv("OPENAI_API_KEY")))


def main() -> None:
    """콘솔 메뉴를 반복 실행합니다."""
    # while True는 사용자가 0번 종료를 선택할 때까지 메뉴를 계속 보여 주기 위해 사용합니다.
    while True:
        # 사용 가능한 기능 목록을 출력합니다.
        print("\n[Agent Loop 콘솔 실습 메뉴]")
        # common.py 상태 확인 메뉴입니다.
        print("1. common.py 공통 모듈 상태 확인")        
        # Torch 재고 분석 메뉴입니다.
        print("2. Torch 재고/재주문 기준 분석")
        # 로컬 에이전트 루프 메뉴입니다.
        print("3. API 없이 로컬 Agent Loop 실행")
        # Gemini API 메뉴입니다.
        print("4. Gemini API Agent Loop 실행")
        # OpenAI API 메뉴입니다.
        print("5. OpenAI API Agent Loop 실행")
        # 종료 메뉴입니다.
        print("0. 종료")

        # 사용자 입력을 받아 앞뒤 공백을 제거합니다.
        choice = input("메뉴 번호 입력: ").strip()

        # 0번이면 반복문을 종료합니다.
        if choice == "0":
            # 종료 메시지를 출력합니다.
            print("프로그램을 종료합니다.")
            # 반복문을 빠져나갑니다.
            break

        # 1번 메뉴는 common.py 상태를 확인합니다.
        if choice == "1":
            # 제목을 출력합니다.
            print_title("1. common.py 공통 모듈 상태 확인")
            # 상태 확인 함수를 실행합니다.
            show_common_status()

        # 2번 메뉴는 Torch 분석을 실행합니다.
        elif choice == "2":
            # 제목을 출력합니다.
            print_title("2. Torch 재고/재주문 기준 분석")
            # Torch 실습 함수를 실행합니다.
            run_torch_inventory_demo()

        # 3번 메뉴는 API 없이 로컬 루프를 실행합니다.
        elif choice == "3":
            # 제목을 출력합니다.
            print_title("3. API 없이 로컬 Agent Loop 실행")
            # 로컬 에이전트 실습을 실행합니다.
            run_local_agent_demo()

        # 4번 메뉴는 Gemini API 루프를 실행합니다.
        elif choice == "4":
            # 제목을 출력합니다.
            print_title("4. Gemini API Agent Loop 실행")
            # Gemini API 실습을 실행합니다.
            run_gemini_agent_demo()

        # 5번 메뉴는 OpenAI API 루프를 실행합니다.
        elif choice == "5":
            # 제목을 출력합니다.
            print_title("5. OpenAI API Agent Loop 실행")
            # OpenAI API 실습을 실행합니다.
            run_openai_agent_demo()

        # 정의되지 않은 번호를 입력하면 안내합니다.
        else:
            # 잘못된 입력 메시지를 출력합니다.
            print("올바른 메뉴 번호를 입력하세요.")


# 이 파일을 직접 실행했을 때만 main 함수를 호출합니다.
if __name__ == "__main__":
    # 콘솔 메뉴 프로그램을 시작합니다.
    main()
