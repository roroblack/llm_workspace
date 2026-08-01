# -*- coding: utf-8 -*-
"""PyCharm에서 바로 실행하는 멀티에이전트 Supervisor 콘솔 애플리케이션입니다."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# 현재 main.py가 있는 code 폴더를 Python 모듈 검색 경로에 추가합니다.
CODE_DIR = Path(__file__).resolve().parent

# 직접 실행과 PyCharm 실행 구성 모두에서 같은 모듈을 찾도록 경로를 보정합니다.
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

# 제공된 common.py의 공통 경로 및 모델 설정을 가져옵니다.
from common import DATA, GEMINI_MODEL, ROOT
# CSV 도구를 직접 실행하기 위한 함수를 가져옵니다.
from data_repository import search_faq, search_products
# 중앙 Supervisor 클래스를 가져옵니다.
from supervisor import Supervisor
# PyTorch 기반 라우팅 평가 함수와 테스트셋을 가져옵니다.
from torch_evaluation import TESTSET, evaluate_predictions, evaluate_rule_router

# 현재 콘솔 세션에서 사용할 기본 LLM 공급자입니다.
CURRENT_PROVIDER = "gemini"


def print_title(title: str) -> None:
    """메뉴 실행 결과를 구분하기 위한 제목 선을 출력합니다."""
    # 가독성을 위해 빈 줄과 구분선을 출력합니다.
    print("\n" + "=" * 78)
    # 전달받은 제목을 출력합니다.
    print(title)
    # 제목 아래 구분선을 출력합니다.
    print("=" * 78)


def show_menu() -> None:
    """HTML 설명 조회 항목 없이 실행 실습 메뉴만 출력합니다."""
    # 현재 선택된 LLM 공급자를 메뉴 상단에 표시합니다.
    print(f"\n[현재 LLM 공급자: {CURRENT_PROVIDER}]")
    # 앱에서 직접 실행할 수 있는 실습 기능만 출력합니다.
    print("1. 공통 환경 및 API 키 로드 상태 확인")
    print("2. LLM 공급자 선택 (Gemini / OpenAI)")
    print("3. 추천 도구 단독 실행 (API 호출 없음)")
    print("4. 정책 FAQ 도구 단독 실행 (API 호출 없음)")
    print("5. 추천 전문 에이전트 실행")
    print("6. 정책 전문 에이전트 실행")
    print("7. Supervisor 규칙 라우터 실행")
    print("8. Supervisor LLM 라우터 실행")
    print("9. Supervisor 하이브리드 라우터 실행")
    print("10. PyTorch 규칙 라우터 정확도 평가")
    print("11. 규칙/LLM/하이브리드 라우터 비교")
    print("0. 종료")


def show_environment() -> None:
    """common.py가 계산한 경로와 환경변수 로드 상태를 출력합니다."""
    # 결과 영역 제목을 출력합니다.
    print_title("공통 환경 확인")
    # 프로젝트 루트 경로를 출력합니다.
    print("ROOT:", ROOT)
    # 데이터 폴더 경로와 존재 여부를 출력합니다.
    print("DATA:", DATA, "(존재:", DATA.exists(), ")")
    # 제공된 common.py가 선택한 Gemini 모델명을 출력합니다.
    print("GEMINI_MODEL:", GEMINI_MODEL)
    # 실제 키 값은 노출하지 않고 설정 여부만 출력합니다.
    print("GOOGLE_API_KEY 설정:", bool(os.getenv("GOOGLE_API_KEY")))
    # OpenAI 키도 값이 아닌 설정 여부만 출력합니다.
    print("OPENAI_API_KEY 설정:", bool(os.getenv("OPENAI_API_KEY")))


def select_provider() -> None:
    """현재 콘솔 세션에서 사용할 LLM 공급자를 변경합니다."""
    # 함수 안에서 전역 공급자 값을 수정하겠다고 선언합니다.
    global CURRENT_PROVIDER

    # 사용자가 선택할 수 있는 공급자 목록을 출력합니다.
    print("\n1. Gemini")
    print("2. OpenAI")

    # 사용자 선택 문자열을 입력받고 공백을 제거합니다.
    choice = input("선택: ").strip()

    # 1번을 선택하면 common.py의 기본 공급자인 gemini를 설정합니다.
    if choice == "1":
        CURRENT_PROVIDER = "gemini"
    # 2번을 선택하면 openai 공급자를 설정합니다.
    elif choice == "2":
        CURRENT_PROVIDER = "openai"
    # 그 외 입력은 설정을 변경하지 않고 안내합니다.
    else:
        print("잘못된 선택입니다. 기존 설정을 유지합니다.")
        return

    # 변경된 공급자를 사용자에게 확인시킵니다.
    print(f"LLM 공급자를 '{CURRENT_PROVIDER}'로 변경했습니다.")


def run_tool(tool_type: str) -> None:
    """LLM 호출 없이 CSV 검색 도구 자체의 동작을 확인합니다."""
    # 추천 도구를 실행하는 경우 카테고리를 입력받습니다.
    if tool_type == "sales":
        keyword = input("상품 카테고리 또는 검색어: ").strip()
        print_title("search_products 실행 결과")
        print(search_products(keyword))
        return

    # 정책 도구를 실행하는 경우 정책 검색어를 입력받습니다.
    keyword = input("정책 검색어: ").strip()
    print_title("search_faq 실행 결과")
    print(search_faq(keyword))


def run_specialist(target: str) -> None:
    """Supervisor 라우팅 없이 선택한 전문 에이전트를 직접 실행합니다."""
    # API 키 및 모델 초기화가 필요한 시점에 Supervisor 객체를 생성합니다.
    supervisor = Supervisor(CURRENT_PROVIDER)

    # 사용자 질문을 입력받습니다.
    question = input("고객 질문: ").strip()

    # Supervisor 내부 딕셔너리에서 선택한 전문 에이전트를 가져옵니다.
    agent = supervisor.agents[target]

    # 전문 에이전트의 검색어 추출, 도구 실행, 답변 생성을 수행합니다.
    result = agent.run(question)

    # 실행 추적 정보를 보기 쉽게 출력합니다.
    print_title(f"{target} 전문 에이전트 실행 결과")
    print("에이전트:", result.agent_name)
    print("사용 도구:", result.tool_name)
    print("도구 입력:", result.tool_input)
    print("\n[도구 근거]\n" + result.evidence)
    print("\n[최종 답변]\n" + result.answer)


def run_supervisor(mode: str) -> None:
    """선택한 라우팅 방식으로 Supervisor 전체 흐름을 실행합니다."""
    # 현재 공급자에 맞는 Supervisor와 두 전문 에이전트를 생성합니다.
    supervisor = Supervisor(CURRENT_PROVIDER)

    # 라우팅할 고객 질문을 입력받습니다.
    question = input("고객 질문: ").strip()

    # Supervisor가 질문을 분류하고 담당 에이전트에 위임하도록 실행합니다.
    result = supervisor.run(question, mode=mode)  # type: ignore[arg-type]

    # 중앙 라우팅과 전문 에이전트 실행 내용을 단계별로 출력합니다.
    print_title(f"Supervisor {mode} 라우팅 결과")
    print("라우팅 대상:", result.route.target)
    print("판단 방식:", result.route.method)
    print("판단 근거:", result.route.reason)
    print("라우팅 LLM 호출:", result.route.llm_calls, "회")
    print("전문 에이전트:", result.agent_result.agent_name)
    print("사용 도구:", result.agent_result.tool_name)
    print("도구 입력:", result.agent_result.tool_input)
    print("\n[도구 근거]\n" + result.agent_result.evidence)
    print("\n[최종 답변]\n" + result.agent_result.answer)


def evaluate_rule() -> None:
    """외부 API 없이 규칙 라우터의 정확도를 PyTorch로 계산합니다."""
    # 규칙 라우터 평가 함수를 호출합니다.
    result = evaluate_rule_router()

    # 평가 개요를 출력합니다.
    print_title("PyTorch 규칙 라우터 평가")
    print(f"정확도: {result.correct}/{result.total} ({result.accuracy * 100:.1f}%)")
    print("LLM 호출:", result.llm_calls, "회")

    # 각 질문의 정답과 예측을 나란히 출력합니다.
    for (question, gold), predicted in zip(TESTSET, result.predictions):
        mark = "O" if gold == predicted else "X"
        print(f"[{mark}] {question} | 정답={gold} | 예측={predicted}")


def compare_routers() -> None:
    """동일한 테스트셋으로 규칙, LLM, 하이브리드 라우터를 비교합니다."""
    # 비교에는 실제 LLM 호출이 필요하므로 현재 공급자의 Supervisor를 생성합니다.
    supervisor = Supervisor(CURRENT_PROVIDER)

    # API 호출이 없는 규칙 라우터 결과를 먼저 계산합니다.
    rule_result = evaluate_rule_router()

    # LLM 라우터 예측과 호출 횟수를 저장할 변수를 준비합니다.
    llm_predictions: list[str] = []
    llm_calls = 0

    # 하이브리드 라우터 예측과 호출 횟수를 저장할 변수를 준비합니다.
    hybrid_predictions: list[str] = []
    hybrid_calls = 0

    # 같은 테스트 질문을 두 라우터에 각각 전달합니다.
    for question, _gold in TESTSET:
        # 모든 질문을 LLM으로 분류합니다.
        llm_decision = supervisor.decide(question, "llm")
        llm_predictions.append(llm_decision.target)
        llm_calls += llm_decision.llm_calls

        # 명확한 질문은 규칙, 애매한 질문은 LLM으로 분류합니다.
        hybrid_decision = supervisor.decide(question, "hybrid")
        hybrid_predictions.append(hybrid_decision.target)
        hybrid_calls += hybrid_decision.llm_calls

    # LLM 라우터 예측을 PyTorch 텐서로 평가합니다.
    llm_result = evaluate_predictions(
        name="LLM 라우터",
        predictions=llm_predictions,
        llm_calls=llm_calls,
    )

    # 하이브리드 라우터 예측도 같은 방식으로 평가합니다.
    hybrid_result = evaluate_predictions(
        name="하이브리드 라우터",
        predictions=hybrid_predictions,
        llm_calls=hybrid_calls,
    )

    # 세 라우터의 정확도와 호출 횟수를 한눈에 비교하여 출력합니다.
    print_title("규칙 / LLM / 하이브리드 라우터 비교")
    for result in (rule_result, llm_result, hybrid_result):
        print(
            f"{result.name:<14} | 정확도 {result.correct}/{result.total} "
            f"({result.accuracy * 100:5.1f}%) | LLM 호출 {result.llm_calls}회"
        )


def main() -> None:
    """사용자가 종료할 때까지 콘솔 메뉴를 반복 실행합니다."""
    # 프로그램 시작 메시지를 출력합니다.
    print("멀티에이전트 Supervisor 콘솔 실습 앱")
    print("HTML 설명 조회 메뉴 없이 실행 실습만 제공합니다.")

    # 사용자가 0을 입력할 때까지 메뉴를 반복합니다.
    while True:
        # 현재 메뉴를 출력합니다.
        show_menu()

        # 메뉴 번호를 문자열로 입력받습니다.
        choice = input("메뉴 선택: ").strip()

        # 각 메뉴 번호에 맞는 함수를 실행합니다.
        try:
            if choice == "1":
                show_environment()
            elif choice == "2":
                select_provider()
            elif choice == "3":
                run_tool("sales")
            elif choice == "4":
                run_tool("policy")
            elif choice == "5":
                run_specialist("sales")
            elif choice == "6":
                run_specialist("policy")
            elif choice == "7":
                run_supervisor("rule")
            elif choice == "8":
                run_supervisor("llm")
            elif choice == "9":
                run_supervisor("hybrid")
            elif choice == "10":
                evaluate_rule()
            elif choice == "11":
                compare_routers()
            elif choice == "0":
                print("프로그램을 종료합니다.")
                break
            else:
                print("0~11 사이의 메뉴 번호를 입력해 주세요.")
        # 설정 누락, API 오류, 입력 오류가 발생해도 콘솔 프로그램 전체가 종료되지 않게 처리합니다.
        except Exception as error:
            print(f"\n[실행 오류] {type(error).__name__}: {error}")


# 이 파일을 직접 실행했을 때만 main 함수를 호출합니다.
if __name__ == "__main__":
    main()
