# -*- coding: utf-8 -*-
"""Final System 핵심 코드를 메뉴로 실행하는 PyCharm 콘솔 앱입니다."""

# 프로젝트 code 폴더를 파이썬 모듈 검색 경로에 추가하기 위해 sys를 가져옵니다.
import sys
# 운영체제와 무관하게 경로를 처리하기 위해 pathlib를 가져옵니다.
from pathlib import Path

# 현재 main.py가 있는 프로젝트 루트 경로를 계산합니다.
ROOT = Path(__file__).resolve().parent
# code 폴더를 문자열로 변환해 모듈 검색 경로 맨 앞에 추가합니다.
sys.path.insert(0, str(ROOT / "code"))

# 선택된 공급자를 읽고 변경하기 위한 함수를 가져옵니다.
from app_context import get_provider_label, set_provider
# 설정과 구조적 로깅 메뉴에서 사용할 함수를 가져옵니다.
from config_service import load_config, setup_logging
# API 없이 직접 실행할 세 가지 실데이터 조회 함수를 가져옵니다.
from data_tools import get_order_status_raw, get_stock_raw, search_faq_raw
# 실습문제 해답 실행 함수를 가져옵니다.
from exercises import run_exchange_exercise, run_memory_isolation_exercise
# 정책 PDF 목록 확인 함수를 가져옵니다.
from policy_rag import list_policy_pdfs


def select_provider() -> None:
    """OpenAI 또는 Gemini 중 사용할 LLM 공급자를 선택합니다."""
    # 선택 화면 제목을 출력합니다.
    print("\n[LLM 공급자 선택]")
    # Gemini 선택 항목을 출력합니다.
    print("1. Google Gemini")
    # OpenAI 선택 항목을 출력합니다.
    print("2. OpenAI")
    # 잘못된 값이 들어오면 다시 입력받기 위해 반복합니다.
    while True:
        # 사용자의 메뉴 입력을 문자열로 받습니다.
        choice = input("선택 [기본 1]: ").strip() or "1"
        # 1번이면 Gemini를 현재 공급자로 저장합니다.
        if choice == "1":
            set_provider("gemini")
            break
        # 2번이면 OpenAI를 현재 공급자로 저장합니다.
        if choice == "2":
            set_provider("openai")
            break
        # 다른 입력이면 지원되는 번호를 안내합니다.
        print("1 또는 2를 입력해 주세요.")
    # 최종 선택된 공급자 표시명을 출력합니다.
    print(f"선택된 공급자: {get_provider_label()}")


def show_menu() -> None:
    """HTML 설명이 아니라 실제 핵심 코드 실행 항목만 출력합니다."""
    # 메뉴 구분선을 출력합니다.
    print("\n" + "=" * 72)
    # 현재 선택된 공급자를 포함한 앱 제목을 출력합니다.
    print(f"제30강 Final System 콘솔 앱 | LLM: {get_provider_label()}")
    # 메뉴 구분선을 다시 출력합니다.
    print("=" * 72)
    # data.zip에서 추출한 주요 데이터와 정책 PDF 확인 메뉴를 출력합니다.
    print("1. data.zip 핵심 데이터와 정책 PDF 확인")
    # 주문 CSV를 직접 조회하는 핵심 도구 메뉴를 출력합니다.
    print("2. 주문 상태 도구 실행")
    # 재고 CSV를 직접 조회하는 핵심 도구 메뉴를 출력합니다.
    print("3. 재고 조회 도구 실행")
    # FAQ CSV를 직접 검색하는 핵심 도구 메뉴를 출력합니다.
    print("4. FAQ 검색 도구 실행")
    # OpenAI/Gemini 임베딩을 이용해 정책 RAG 도구를 만드는 메뉴를 출력합니다.
    print("5. 정책 RAG 도구 빌드 확인")
    # 도구, RAG, 메모리를 결합한 최종 단일 질문 메뉴를 출력합니다.
    print("6. 통합 에이전트 단일 질문")
    # 같은 thread_id로 세 능력을 시연하는 메뉴를 출력합니다.
    print("7. 멀티턴 시나리오 데모")
    # 잘못된 주문, 오타 상품, 없는 FAQ를 직접 검증하는 메뉴를 출력합니다.
    print("8. 에러 케이스 도구 단위 검증")
    # 교환 쓰기 도구 추가 실습 해답 메뉴를 출력합니다.
    print("9-1. 실습문제 1 해답: 교환 신청 도구")
    # thread_id별 메모리 격리 실습 해답 메뉴를 출력합니다.
    print("9-2. 실습문제 2 해답: 메모리 격리")
    # 실행 중 LLM 공급자를 변경하는 메뉴를 출력합니다.
    print("10. OpenAI/Gemini 공급자 다시 선택")
    # 프로그램 종료 메뉴를 출력합니다.
    print("0. 종료")


def menu_data_check() -> None:
    """핵심 CSV 열과 정책 PDF 개수를 확인합니다."""
    # pandas를 이 메뉴에서만 사용하도록 지연 import합니다.
    import pandas as pd
    # 확인할 핵심 CSV 파일 이름을 리스트로 정의합니다.
    filenames = ["orders.csv", "inventory.csv", "faq.csv"]
    # 각 CSV 파일을 순회합니다.
    for filename in filenames:
        # 프로젝트 data 폴더 기준 전체 경로를 구성합니다.
        path = ROOT / "data" / filename
        # CSV를 읽어 DataFrame으로 변환합니다.
        frame = pd.read_csv(path)
        # 파일명, 행 수와 열 이름을 출력합니다.
        print(f"\n[{filename}] 행={len(frame):,}, 열={list(frame.columns)}")
        # 실제 데이터 형식을 확인할 수 있도록 첫 두 행을 출력합니다.
        print(frame.head(2).to_string(index=False))
    # 정책 문서 폴더의 모든 PDF를 가져옵니다.
    pdfs = list_policy_pdfs()
    # PDF 파일 개수를 출력합니다.
    print(f"\n[정책 PDF] {len(pdfs)}개")
    # 각 PDF의 실제 저장 파일명을 출력합니다.
    for pdf in pdfs:
        print(" -", pdf.name)


def menu_policy_build() -> None:
    """현재 공급자의 임베딩으로 정책 RAG 도구를 실제 생성합니다."""
    # 설정을 읽습니다.
    config = load_config()
    # 구조적 로거를 생성합니다.
    logger = setup_logging(config)
    # RAG 빌더를 지연 import합니다.
    from policy_rag import build_policy_tool
    # 정책 PDF 임베딩과 FAISS 인덱싱을 실행합니다.
    tool = build_policy_tool(config, logger)
    # 생성된 도구 이름과 설명을 출력합니다.
    print("정책 RAG 도구 생성 완료:", tool.name)
    # 도구 설명을 출력해 LLM이 어떤 용도로 사용하는지 확인합니다.
    print("도구 설명:", tool.description)


def menu_agent_chat() -> None:
    """사용자 질문 한 건을 통합 에이전트에 전달합니다."""
    # 통합 answer 함수를 API 사용 시점에 지연 import합니다.
    from final_agent import answer
    # 대화 세션을 구분할 thread_id를 입력받습니다.
    thread_id = input("thread_id [기본 console-user]: ").strip() or "console-user"
    # 에이전트에 전달할 질문을 입력받습니다.
    message = input("질문: ").strip()
    # 빈 질문이면 호출하지 않고 안내합니다.
    if not message:
        print("질문을 입력해 주세요.")
        return
    # 도구, RAG와 메모리가 통합된 답변을 생성해 출력합니다.
    print("\n상담원:", answer(message, thread_id=thread_id))


def menu_multiturn() -> None:
    """RAG, 주문 도구와 메모리를 같은 thread_id에서 순차 시연합니다."""
    # 통합 answer 함수를 지연 import합니다.
    from final_agent import answer
    # 한 고객의 대화 세션을 나타낼 고정 thread_id를 지정합니다.
    thread_id = "demo-user-1001"
    # 세 능력을 순서대로 확인할 질문 목록을 정의합니다.
    turns = ["환불 절차 알려줘", "내 주문 O000050은?", "아까 그 정책 다시 알려줘"]
    # 질문 순서와 내용을 함께 순회합니다.
    for number, question in enumerate(turns, start=1):
        # 턴 구분선을 출력합니다.
        print("\n" + "-" * 72)
        # 현재 턴의 고객 질문을 출력합니다.
        print(f"[턴 {number}] 고객: {question}")
        # 같은 thread_id로 답변해 이전 문맥을 유지합니다.
        print("상담원:", answer(question, thread_id=thread_id))


def menu_error_cases() -> None:
    """LLM 없이 도구의 1차 방어선이 잘 작동하는지 검증합니다."""
    # 존재하지 않는 주문번호를 조회하고 거짓 상태를 만들지 않는지 확인합니다.
    print("\n[없는 주문]", get_order_status_raw("O999999"))
    # 오타가 있는 상품명을 조회하고 임의 수량을 만들지 않는지 확인합니다.
    print("\n[오타 상품]", get_stock_raw("로봇청쇼기"))
    # 데이터에 없는 FAQ를 검색하고 관련 정보 없음 문구를 확인합니다.
    print("\n[없는 FAQ]", search_faq_raw("우주배송"))


def main() -> None:
    """공급자 선택 후 사용자가 종료할 때까지 메뉴를 반복 실행합니다."""
    # 앱 시작 시 OpenAI와 Gemini 중 하나를 선택받습니다.
    select_provider()
    # 종료 메뉴가 선택될 때까지 반복합니다.
    while True:
        # 핵심 코드 실행 메뉴를 출력합니다.
        show_menu()
        # 사용자의 메뉴 번호를 입력받습니다.
        choice = input("메뉴 선택: ").strip()
        # 각 메뉴 실행 중 오류가 나도 전체 앱이 종료되지 않도록 예외 처리합니다.
        try:
            # 1번은 데이터와 PDF 구조를 확인합니다.
            if choice == "1":
                menu_data_check()
            # 2번은 주문번호를 입력받아 주문 도구를 실행합니다.
            elif choice == "2":
                print(get_order_status_raw(input("주문번호 [예: O000050]: ")))
            # 3번은 상품명을 입력받아 재고 도구를 실행합니다.
            elif choice == "3":
                print(get_stock_raw(input("상품명: ")))
            # 4번은 키워드를 입력받아 FAQ 검색 도구를 실행합니다.
            elif choice == "4":
                print(search_faq_raw(input("FAQ 키워드: ")))
            # 5번은 실제 임베딩 API를 사용하는 정책 RAG 도구를 빌드합니다.
            elif choice == "5":
                menu_policy_build()
            # 6번은 통합 에이전트에 자유 질문을 전달합니다.
            elif choice == "6":
                menu_agent_chat()
            # 7번은 멀티턴 데모를 실행합니다.
            elif choice == "7":
                menu_multiturn()
            # 8번은 잘못된 입력에 대한 도구 단위 에러 처리를 검증합니다.
            elif choice == "8":
                menu_error_cases()
            # 9-1은 교환 신청 도구 실습 해답을 실행합니다.
            elif choice == "9-1":
                run_exchange_exercise()
            # 9-2는 서로 다른 thread_id의 메모리 격리를 검증합니다.
            elif choice == "9-2":
                run_memory_isolation_exercise()
            # 10번은 공급자를 다시 선택하고 에이전트 캐시를 초기화합니다.
            elif choice == "10":
                select_provider()
                # 공급자가 바뀌었으므로 기존 RAG와 LLM 에이전트 캐시를 제거합니다.
                from final_agent import reset_agent
                # 다음 호출 때 새 공급자로 다시 빌드하도록 초기화합니다.
                reset_agent()
            # 0번은 반복문을 종료합니다.
            elif choice == "0":
                print("프로그램을 종료합니다.")
                break
            # 등록되지 않은 입력이면 메뉴 번호를 다시 안내합니다.
            else:
                print("올바른 메뉴 번호를 입력해 주세요.")
        # API 키 누락처럼 common.py가 SystemExit을 발생시키는 경우 메시지만 출력합니다.
        except SystemExit as error:
            print(error)
        # 패키지 미설치, API 오류, 데이터 오류 등 일반 예외를 잡아 앱 종료를 막습니다.
        except Exception as error:
            print(f"[실행 오류] {type(error).__name__}: {error}")


# 이 파일을 직접 실행했을 때만 main 함수를 호출합니다.
if __name__ == "__main__":
    main()
