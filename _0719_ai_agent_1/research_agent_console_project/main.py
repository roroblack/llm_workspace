# -*- coding: utf-8 -*-
"""PyCharm에서 바로 실행하는 제22강 리서치 에이전트 콘솔 앱입니다."""

# code 폴더의 모듈을 불러오기 위해 pathlib과 sys를 사용합니다.
import pathlib
import sys

# 현재 main.py가 있는 프로젝트 루트 경로를 계산합니다.
ROOT = pathlib.Path(__file__).resolve().parent
# 공통 기능 모듈이 들어 있는 code 폴더 경로를 계산합니다.
CODE_DIR = ROOT / "code"
# code 폴더를 Python 모듈 검색 경로의 앞쪽에 추가합니다.
sys.path.insert(0, str(CODE_DIR))

# 메뉴에서 선택한 모델 공급자를 저장하고 화면에 표시하는 함수를 가져옵니다.
from app_context import provider_label, set_provider
# 교차 검증 기능과 구조화 판정 결과를 가져옵니다.
from cross_check_service import cross_check
# data.zip 기반 보고서 기능을 가져옵니다.
from data_report_service import make_competitor_report, make_internal_sales_report
# 심층 조사 기능을 가져옵니다.
from deep_research import deep_research_and_save
# 실습문제 해답 실행 함수를 가져옵니다.
from exercises import exercise_1_competitor_csv, exercise_2_multiquery
# 검색 없는 LLM 비교, 검색 에이전트, 폴백, 저장 기능을 가져옵니다.
from research_service import (
    llm_only_latest_demo,
    run_research_and_save,
)


def print_line(char: str = "=", length: int = 72) -> None:
    """콘솔 메뉴와 결과를 구분하는 선을 출력합니다."""
    # 지정한 문자를 지정 길이만큼 반복해 출력합니다.
    print(char * length)


def pause() -> None:
    """사용자가 결과를 읽은 뒤 메뉴로 돌아가도록 입력을 기다립니다."""
    # Enter를 누를 때까지 프로그램 흐름을 잠시 멈춥니다.
    input("\n[Enter] 키를 누르면 메뉴로 돌아갑니다.")


def print_preview(body: str, max_length: int = 1800) -> None:
    """긴 리포트의 앞부분을 콘솔에 보기 좋게 출력합니다."""
    # 결과 영역 시작선을 출력합니다.
    print_line()
    # 지정 길이까지만 출력해 콘솔이 지나치게 길어지는 것을 막습니다.
    print(body[:max_length])
    # 본문이 잘렸으면 파일에서 전체 내용을 확인하라는 안내를 덧붙입니다.
    if len(body) > max_length:
        print("\n... [콘솔 미리보기 생략: 저장된 마크다운 파일에서 전체 내용을 확인하세요.] ...")
    # 결과 영역 종료선을 출력합니다.
    print_line()


def ask_topic(default: str = "경쟁 무선이어버드 시장 동향") -> str:
    """사용자에게 조사 주제를 입력받고 빈 입력이면 기본 주제를 반환합니다."""
    # 현재 기본값을 함께 보여 주어 바로 Enter로 실행할 수 있게 합니다.
    topic = input(f"조사 주제 입력 [기본: {default}]: ").strip()
    # 값이 있으면 사용자 입력을, 없으면 기본 주제를 반환합니다.
    return topic or default


def select_provider() -> bool:
    """OpenAI 또는 Gemini를 선택하고, 종료 선택 시 False를 반환합니다."""
    while True:
        # 공급자 선택 화면을 구분합니다.
        print_line()
        print("제22강 Research Agent — LLM 공급자 선택")
        print_line()
        print("1. OpenAI 사용")
        print("2. Gemini 사용")
        print("0. 프로그램 종료")

        # 사용자의 메뉴 번호를 문자열로 입력받습니다.
        choice = input("선택: ").strip()

        # 1번이면 OpenAI를 앱 컨텍스트에 저장합니다.
        if choice == "1":
            set_provider("openai")
            return True

        # 2번이면 Gemini를 앱 컨텍스트에 저장합니다.
        if choice == "2":
            set_provider("gemini")
            return True

        # 0번이면 호출자에게 종료 의사를 알립니다.
        if choice == "0":
            return False

        # 정의되지 않은 입력에는 다시 선택하도록 안내합니다.
        print("[입력 오류] 0, 1, 2 중 하나를 입력하세요.")


def print_main_menu() -> None:
    """HTML 설명 메뉴를 제외하고 중요한 실행 코드 메뉴만 출력합니다."""
    print_line()
    print(f"제22강 Research Agent 콘솔 앱 | 현재 모델: {provider_label()}")
    print_line()
    print("1. 검색 없는 LLM의 최신 시장 동향 응답 확인")
    print("2. 웹 검색 리서치 에이전트 + 자동 폴백 + 리포트 저장")
    print("3. 검색 실패 상황을 강제하여 폴백 코드 확인")
    print("4. 복잡한 주제 하위 질의 분해 + 심층 조사 + 저장")
    print("5. 검색 결과 교차 검증 및 신뢰도 판정")
    print("6. data.zip 경쟁사 CSV 기반 리포트 생성")
    print("7. data.zip 월별 매출·상품 데이터 기반 내부 리포트")
    print("8-1. 실습문제 해답 1 — 경쟁사 CSV 리포트")
    print("8-2. 실습문제 해답 2 — 다중 하위 질의 통합")
    print("9. OpenAI / Gemini 다시 선택")
    print("0. 프로그램 종료")


def run_menu() -> bool:
    """현재 선택한 공급자로 주요 코드 메뉴를 반복 실행합니다."""
    while True:
        # 매 반복마다 최신 메뉴를 출력합니다.
        print_main_menu()
        # 사용자의 메뉴 선택값을 입력받습니다.
        choice = input("선택: ").strip().lower()

        try:
            # 검색 없는 LLM의 최신성 한계를 직접 확인합니다.
            if choice == "1":
                topic = ask_topic()
                body = llm_only_latest_demo(topic)
                print_preview(body)
                pause()

            # 웹 검색 에이전트를 실행하고 결과를 마크다운으로 저장합니다.
            elif choice == "2":
                topic = ask_topic()
                body, path, used_fallback, elapsed = run_research_and_save(topic)
                print_preview(body)
                print(f"[저장 완료] {path}")
                print(f"[실행 정보] 소요 시간: {elapsed:.2f}초 / 폴백 사용: {used_fallback}")
                pause()

            # 교육용으로 검색 실패 분기를 강제해 폴백 코드를 확인합니다.
            elif choice == "3":
                topic = ask_topic()
                body, path, used_fallback, elapsed = run_research_and_save(topic, force_fallback=True)
                print_preview(body)
                print(f"[저장 완료] {path}")
                print(f"[실행 정보] 소요 시간: {elapsed:.2f}초 / 폴백 사용: {used_fallback}")
                pause()

            # 큰 주제를 자동 분해하고 여러 검색 결과를 종합합니다.
            elif choice == "4":
                topic = ask_topic()
                body, path, queries, fallback_count = deep_research_and_save(topic)
                print_preview(body)
                print(f"[하위 질의 수] {len(queries)}")
                print(f"[검색 폴백 횟수] {fallback_count}")
                print(f"[저장 완료] {path}")
                pause()

            # 같은 주장을 서로 다른 검색어로 검증합니다.
            elif choice == "5":
                default_claim = "최근 무선이어버드 시장은 ANC 기능 중심으로 성장하고 있다."
                claim = input(f"검증할 주장 [기본: {default_claim}]: ").strip() or default_claim
                default_a = "무선이어버드 시장 성장 노이즈 캔슬링"
                query_a = input(f"검색어 A [기본: {default_a}]: ").strip() or default_a
                default_b = "TWS 이어버드 ANC 트렌드 2026"
                query_b = input(f"검색어 B [기본: {default_b}]: ").strip() or default_b
                verdict, _, _, fallback_count = cross_check(claim, query_a, query_b)
                print_line()
                print(f"[일치 여부] {verdict.agree}")
                print(f"[신뢰도] {verdict.confidence}")
                print(f"[판정 근거] {verdict.reason}")
                print(f"[주의 사항] {verdict.caution}")
                print(f"[검색 폴백 횟수] {fallback_count}")
                print_line()
                pause()

            # data.zip의 competitor_data.csv로 검색 없는 리포트를 생성합니다.
            elif choice == "6":
                body, path, companies = make_competitor_report()
                print_preview(body)
                print(f"[분석 경쟁사] {', '.join(companies)}")
                print(f"[저장 완료] {path}")
                pause()

            # 월별 매출과 상품 CSV를 함께 사용한 내부 분석 리포트를 생성합니다.
            elif choice == "7":
                body, path = make_internal_sales_report()
                print_preview(body)
                print(f"[저장 완료] {path}")
                pause()

            # HTML의 실습문제 1 해답을 별도 메뉴로 실행합니다.
            elif choice in {"8-1", "81"}:
                body, path, companies = exercise_1_competitor_csv()
                print_preview(body)
                print(f"[검증 대상 경쟁사 수] {len(companies)}")
                print(f"[저장 완료] {path}")
                pause()

            # HTML의 실습문제 2 해답을 별도 메뉴로 실행합니다.
            elif choice in {"8-2", "82"}:
                body, path, subtopics, fallback_count = exercise_2_multiquery()
                print_preview(body)
                print(f"[하위 주제] {', '.join(subtopics)}")
                print(f"[검색 폴백 횟수] {fallback_count}")
                print(f"[저장 완료] {path}")
                pause()

            # 공급자 선택 화면으로 돌아갑니다.
            elif choice == "9":
                return True

            # 프로그램 전체를 종료합니다.
            elif choice == "0":
                return False

            # 정의되지 않은 메뉴 번호에는 오류 안내를 출력합니다.
            else:
                print("[입력 오류] 표시된 메뉴 번호를 입력하세요.")

        except (KeyboardInterrupt, EOFError):
            # Ctrl+C 또는 입력 종료 시 프로그램이 추적 오류를 출력하지 않도록 종료합니다.
            print("\n[종료] 사용자 입력으로 프로그램을 종료합니다.")
            return False

        except Exception as exc:
            # API 키, 네트워크, 패키지, 파일 등의 실행 오류를 메뉴가 죽지 않게 처리합니다.
            print_line("!")
            print(f"[실행 오류] {type(exc).__name__}: {exc}")
            print(".env의 API 키, 인터넷 연결, requirements 설치 상태를 확인하세요.")
            print_line("!")
            pause()


def main() -> None:
    """공급자 선택과 기능 메뉴를 연결하는 프로그램 진입점입니다."""
    # 프로그램 제목을 출력합니다.
    print("제22강 Research Agent PyCharm 콘솔 프로젝트")

    # 사용자가 종료를 선택할 때까지 공급자 선택과 메뉴 실행을 반복합니다.
    while True:
        # 공급자 선택 화면에서 종료를 고르면 반복문을 끝냅니다.
        if not select_provider():
            break

        # 기능 메뉴가 False를 반환하면 프로그램 전체를 종료합니다.
        if not run_menu():
            break

    # 정상 종료 메시지를 출력합니다.
    print("프로그램을 종료합니다.")


# 이 파일을 PyCharm에서 직접 실행했을 때만 main 함수를 호출합니다.
if __name__ == "__main__":
    main()
