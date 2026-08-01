# -*- coding: utf-8 -*-
"""OpenAI와 Gemini를 모두 선택할 수 있는 제28강 콘솔 메뉴입니다."""

# 환경변수 확인을 위해 os를 가져옵니다.
import os
# 설계 스켈레톤 출력 함수를 가져옵니다.
from app.project_design import print_design
# 트레이드오프 예제 실행 함수를 가져옵니다.
from app.tradeoff import run_examples
# 실습문제 완성 함수를 가져옵니다.
from app.exercises import create_design_document, print_exercise_skeleton
# 선택 provider로 설계를 검토하는 함수를 가져옵니다.
from app.llm_review import review_design
# 원본 common.py의 데이터 경로를 가져옵니다.
from app.common_bridge import DATA


def pause() -> None:
    """결과를 읽은 뒤 메뉴로 돌아갈 수 있도록 입력을 기다립니다."""
    # Enter 입력이 들어올 때까지 프로그램 진행을 멈춥니다.
    input("\nEnter를 누르면 메뉴로 돌아갑니다.")


def choose_provider() -> str | None:
    """OpenAI 또는 Gemini provider를 선택하고 문자열로 반환합니다."""
    # provider 선택 안내를 출력합니다.
    print("\n1. OpenAI\n2. Gemini\n0. 이전 메뉴")
    # 사용자의 선택을 문자열로 읽습니다.
    choice = input("LLM 선택: ").strip()
    # 1번이면 OpenAI provider 이름을 반환합니다.
    if choice == "1":
        return "openai"
    # 2번이면 Gemini provider 이름을 반환합니다.
    if choice == "2":
        return "gemini"
    # 그 외 입력은 선택 취소로 처리합니다.
    return None


def show_environment() -> None:
    """원본 common.py가 사용하는 데이터와 API 키 설정 상태를 확인합니다."""
    # 데이터 디렉터리의 실제 경로와 존재 여부를 출력합니다.
    print(f"DATA={DATA} / 존재={DATA.exists()}")
    # 핵심 실습 데이터 파일의 존재 여부를 출력합니다.
    for name in ("support_tickets.csv", "faq.csv", "orders.csv", "inventory.csv"):
        print(f"- {name}: {(DATA / name).exists()}")
    # OpenAI 키가 환경변수에 설정됐는지 값 자체를 노출하지 않고 출력합니다.
    print(f"OPENAI_API_KEY 설정={bool(os.getenv('OPENAI_API_KEY'))}")
    # Gemini 키가 환경변수에 설정됐는지 값 자체를 노출하지 않고 출력합니다.
    print(f"GOOGLE_API_KEY 설정={bool(os.getenv('GOOGLE_API_KEY'))}")


def main() -> None:
    """프로그램이 종료될 때까지 제28강 실행 메뉴를 반복 표시합니다."""
    # 사용자가 종료를 선택할 때까지 메뉴 루프를 반복합니다.
    while True:        
        print("\n" + "=" * 68)
        print("Project Design 실행 확인 콘솔")
        print("=" * 68)
        print("1. 환경·데이터 확인")
        print("2. 통합 CS 에이전트 설계 스켈레톤 실행")
        print("3. 트레이드오프 판단 도우미 실행")
        print("4. 실습문제 1 — 설계 문서 생성")
        print("5. 실습문제 2 — 코드 스켈레톤 실행")
        print("6. OpenAI/Gemini 설계 검토 실행")
        print("0. 종료")
        # 실행할 메뉴 번호를 입력받습니다.
        choice = input("메뉴 선택: ").strip()
        # 예외가 발생해도 전체 콘솔이 종료되지 않도록 실행 구역을 보호합니다.
        try:
            # 1번 메뉴는 환경과 데이터를 확인합니다.
            if choice == "1":
                show_environment()
            # 2번 메뉴는 기본 설계 스켈레톤을 실행합니다.
            elif choice == "2":
                print_design()
            # 3번 메뉴는 여러 설계 시나리오의 도입 판단을 실행합니다.
            elif choice == "3":
                run_examples()
            # 4번 메뉴는 실습문제 1의 마크다운 설계 문서를 생성합니다.
            elif choice == "4":
                print(create_design_document())
            # 5번 메뉴는 실습문제 2의 완성 스켈레톤을 실행합니다.
            elif choice == "5":
                print_exercise_skeleton()
            # 6번 메뉴는 선택한 LLM으로 설계 검토를 실행합니다.
            elif choice == "6":
                provider = choose_provider()
                if provider:
                    print(f"\n[{provider.upper()} 설계 검토 결과]")
                    print(review_design(provider))
            # 0번 메뉴는 반복문을 종료합니다.
            elif choice == "0":
                print("프로그램을 종료합니다.")
                break
            # 정의되지 않은 번호는 다시 입력하도록 안내합니다.
            else:
                print("메뉴 번호를 다시 확인하십시오.")
            # 종료 메뉴가 아닌 경우 결과 확인을 위해 대기합니다.
            if choice != "0":
                pause()
        # API 키 누락처럼 SystemExit로 전달되는 설정 오류를 잡습니다.
        except SystemExit as error:
            print(error)
            pause()
        # 네트워크·패키지·모델 호출 오류를 잡아 콘솔이 계속 실행되게 합니다.
        except Exception as error:
            print(f"[실행 오류] {type(error).__name__}: {error}")
            pause()
