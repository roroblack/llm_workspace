# -*- coding: utf-8 -*-
"""OpenAI와 Gemini를 동일한 실습 메뉴에서 선택·실행하는 콘솔 UI입니다."""

# 기본 파이프라인 실행 함수를 가져옵니다.
from code_app.ai_team import create_nodes, load_competitor_text, run_basic_team
# 조건부 분기, 중간 저장, 두 실습문제 실행 함수를 가져옵니다.
from code_app.conditional_review import run_conditional_team
from code_app.artifact_save import REPORTS_DIR, run_saving_team
from code_app.exercise_reviewer import run_review_exercise
from code_app.exercise_save_all import OUTPUT_DIR, run_save_all_exercise


def print_separator(title: str = "") -> None:
    """메뉴와 결과 영역을 구분하는 제목선을 출력합니다."""
    # 고정 폭의 구분선을 출력합니다.
    print("\n" + "=" * 72)
    # 제목이 전달된 경우 구분선 아래에 제목을 표시합니다.
    if title:
        print(title)
        print("-" * 72)


def select_provider() -> str | None:
    """상위 메뉴에서 OpenAI 또는 Gemini provider를 선택합니다."""
    # 사용자가 볼 모델 공급자 선택 메뉴를 출력합니다.
    print_separator("LangGraph AI Team — LLM 선택")
    print("1. OpenAI 실행 메뉴")
    print("2. Gemini 실행 메뉴")
    print("0. 프로그램 종료")
    # 앞뒤 공백을 제거한 사용자 입력을 받습니다.
    choice = input("선택: ").strip()
    # 1번은 common.py가 지원하는 openai 문자열로 변환합니다.
    if choice == "1":
        return "openai"
    # 2번은 common.py가 지원하는 gemini 문자열로 변환합니다.
    if choice == "2":
        return "gemini"
    # 0번은 종료를 의미하도록 None을 반환합니다.
    if choice == "0":
        return None
    # 정의되지 않은 입력은 안내 후 상위 메뉴를 다시 보여줍니다.
    print("[입력 오류] 0, 1, 2 중 하나를 입력하세요.")
    return ""


def run_provider_menu(provider: str) -> None:
    """선택된 provider에서 실행할 제27강 실습 항목을 반복해서 보여줍니다."""

    # 메뉴 제목에 표시할 공급자 이름을 사람이 읽기 좋은 형태로 변환합니다.
    provider_label = "OpenAI" if provider == "openai" else "Gemini"
    # 사용자가 이전 메뉴를 선택하기 전까지 하위 메뉴를 반복합니다.
    while True:
        print_separator(f"{provider_label} — StateGraph AI Team 실행 메뉴")
        print("1. 경쟁사 CSV 데이터 로드 확인")
        print("2. Researcher 단일 노드 실행")
        print("3. Analyst 단일 노드 실행")
        print("4. Writer 단일 노드 실행")
        print("5. 기본 StateGraph 전체 실행")
        print("6. 조건부 분기 품질 재검토 실행")
        print("7. 중간 산출물 reports 저장 실행")
        print("8. 실습문제 1 — Reviewer/Finalize 노드")
        print("9. 실습문제 2 — 단계별 output 파일 저장")
        print("0. LLM 선택 메뉴로 돌아가기")
        # 실행할 번호를 문자열로 받습니다.
        choice = input("선택: ").strip()
        # 0번이면 현재 하위 메뉴 반복을 끝냅니다.
        if choice == "0":
            return
        try:
            # 데이터 로드 메뉴는 API를 호출하지 않고 제공 CSV만 확인합니다.
            if choice == "1":
                print_separator("경쟁사 데이터")
                print(load_competitor_text())
            # Researcher 단일 노드는 원천 데이터를 정리한 결과만 출력합니다.
            elif choice == "2":
                researcher, _, _ = create_nodes(provider)
                state = {"raw": load_competitor_text(), "analysis": "", "report": ""}
                print_separator("Researcher 결과")
                print(researcher(state)["raw"])
            # Analyst 단일 실행을 위해 Researcher 결과를 먼저 만든 후 분석합니다.
            elif choice == "3":
                researcher, analyst, _ = create_nodes(provider)
                state = {"raw": load_competitor_text(), "analysis": "", "report": ""}
                state.update(researcher(state))
                print_separator("Analyst 결과")
                print(analyst(state)["analysis"])
            # Writer 단일 실행은 앞 단계 산출물이 필요하므로 Researcher와 Analyst를 순서대로 실행합니다.
            elif choice == "4":
                researcher, analyst, writer = create_nodes(provider)
                state = {"raw": load_competitor_text(), "analysis": "", "report": ""}
                state.update(researcher(state))
                state.update(analyst(state))
                print_separator("Writer 결과")
                print(writer(state)["report"])
            # 기본 StateGraph 전체 실행 결과의 report를 출력합니다.
            elif choice == "5":
                final = run_basic_team(provider)
                print_separator("기본 AI Team 최종 리포트")
                print(final["report"])
            # 조건부 분기 결과와 재시도 횟수·최종 판정을 함께 출력합니다.
            elif choice == "6":
                final = run_conditional_team(provider)
                print_separator(f"조건부 그래프 결과 — 판정={final['verdict']}, 재시도={final['retries']}")
                print(final["report"])
            # 저장 래퍼 그래프를 실행하고 실제 reports 경로를 표시합니다.
            elif choice == "7":
                final = run_saving_team(provider)
                print_separator(f"저장 완료: {REPORTS_DIR}")
                print(final["report"])
            # 실습문제 1은 review와 final을 모두 확인하게 합니다.
            elif choice == "8":
                final = run_review_exercise(provider)
                print_separator("Reviewer 검토 의견")
                print(final["review"])
                print_separator("검토 반영 최종본")
                print(final["final"])
            # 실습문제 2는 네 파일 저장 후 최종본과 output 경로를 표시합니다.
            elif choice == "9":
                final = run_save_all_exercise(provider)
                print_separator(f"단계별 저장 완료: {OUTPUT_DIR}")
                print(final["final"])
            # 메뉴 범위 밖의 입력은 오류 메시지를 출력합니다.
            else:
                print("[입력 오류] 0부터 9 사이의 번호를 입력하세요.")
        # API 키 누락, 네트워크, 할당량, 모델 오류 등 실행 예외를 메뉴 전체 종료 없이 처리합니다.
        except Exception as error:
            print_separator("실행 오류")
            print(f"{type(error).__name__}: {error}")


def run_console() -> None:
    """프로그램 종료가 선택될 때까지 provider 선택 메뉴를 반복합니다."""

    # 상위 메뉴를 계속 반복합니다.
    while True:
        # OpenAI/Gemini 중 사용할 provider를 선택받습니다.
        provider = select_provider()
        # None은 사용자가 0번 종료를 선택했다는 의미입니다.
        if provider is None:
            print("프로그램을 종료합니다.")
            return
        # 빈 문자열은 잘못된 입력이므로 하위 메뉴로 진입하지 않습니다.
        if not provider:
            continue
        # 선택한 provider의 실습 메뉴를 실행합니다.
        run_provider_menu(provider)
