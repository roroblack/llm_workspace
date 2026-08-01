# -*- coding: utf-8 -*-
"""PyCharm에서 실행하는 OpenAI/Gemini 선택형 Agent Memory 콘솔 앱입니다."""

# os 모듈은 화면 정리와 같은 운영체제 기능에 사용할 수 있도록 가져옵니다.
import os
# sys 모듈은 예외 발생 시 실행 환경 정보를 다루기 위해 가져옵니다.
import sys
# Path는 프로젝트 경로를 안정적으로 확인하기 위해 사용합니다.
from pathlib import Path

# 프로젝트 루트를 파이썬 모듈 검색 경로의 맨 앞에 추가합니다.
PROJECT_ROOT = Path(__file__).resolve().parent
# PyCharm 실행 위치가 달라도 code 패키지를 찾을 수 있도록 처리합니다.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 제공된 data.zip 기반 고객 데이터 조회 함수를 가져옵니다.
from code.data_service import context_to_prompt, list_sample_customer_ids, load_customer_context
# 메모리 핵심 기능을 구현한 함수들을 가져옵니다.
from code.memory_agent import (
    build_agent,
    build_demo_messages,
    chat,
    manual_memory_turn,
    stateless_call,
    summarize_old,
    trim_recent,
)
# 메시지 객체를 사람이 읽을 수 있는 문자열로 바꾸는 함수를 가져옵니다.
from code.message_utils import message_to_text


def print_title(title: str) -> None:
    """콘솔 기능 제목을 일정한 형식으로 출력합니다."""
    # 기능 구분을 위한 빈 줄과 구분선을 출력합니다.
    print("\n" + "=" * 72)
    # 전달받은 제목을 출력합니다.
    print(title)
    # 제목 아래 구분선을 출력합니다.
    print("=" * 72)


def pause() -> None:
    """사용자가 결과를 확인한 뒤 메뉴로 돌아가게 합니다."""
    # Enter 입력을 기다려 결과 화면이 바로 사라지지 않게 합니다.
    input("\nEnter 키를 누르면 메뉴로 돌아갑니다.")


def choose_provider() -> str | None:
    """OpenAI 또는 Gemini 공급자를 선택합니다."""
    # 공급자 선택 메뉴를 반복 출력합니다.
    while True:
        # 공급자 메뉴 제목을 출력합니다.
        print_title("LLM 공급자 선택")
        # OpenAI 선택 항목을 출력합니다.
        print("1. OpenAI")
        # Gemini 선택 항목을 출력합니다.
        print("2. Gemini")
        # 프로그램 종료 항목을 출력합니다.
        print("0. 종료")
        # 사용자의 선택값을 문자열로 입력받습니다.
        choice = input("선택: ").strip()
        # 1을 선택하면 common.py에서 사용하는 openai 값을 반환합니다.
        if choice == "1":
            return "openai"
        # 2를 선택하면 common.py에서 사용하는 gemini 값을 반환합니다.
        if choice == "2":
            return "gemini"
        # 0을 선택하면 상위 실행 루프 종료를 위해 None을 반환합니다.
        if choice == "0":
            return None
        # 허용되지 않은 값이면 안내 메시지를 출력합니다.
        print("1, 2, 0 중 하나를 입력하십시오.")


def demo_stateless(provider: str) -> None:
    """LLM 호출이 기본적으로 이전 대화를 기억하지 않는 현상을 확인합니다."""
    # 현재 기능 제목을 출력합니다.
    print_title("1. Stateless 호출 비교")
    # 첫 호출에서 사용자 이름을 알려줍니다.
    first = stateless_call(provider, "내 이름은 민준이야. 이 문장에 짧게 답해줘.")
    # 첫 호출 결과를 출력합니다.
    print("[호출 1]", first)
    # 두 번째 호출은 완전히 독립적으로 이름을 질문합니다.
    second = stateless_call(provider, "내 이름이 뭐라고 했지? 이전 대화를 모르면 모른다고 답해.")
    # 두 번째 호출 결과를 출력합니다.
    print("[호출 2]", second)
    # 각 호출에 이전 메시지를 주지 않았다는 관찰점을 출력합니다.
    print("\n관찰: 두 번째 호출에는 첫 번째 대화 기록을 전달하지 않았습니다.")


def demo_manual_memory(provider: str) -> None:
    """메시지 리스트를 직접 누적하여 기억처럼 동작시키는 방식을 확인합니다."""
    # 현재 기능 제목을 출력합니다.
    print_title("2. 수동 대화 기록 누적")
    # 한 세션의 전체 대화를 저장할 빈 리스트를 만듭니다.
    history: list = []
    # 첫 번째 사용자 발화와 모델 응답을 history에 누적합니다.
    print("[1턴]", manual_memory_turn(provider, history, "내 이름은 민준이야."))
    # 두 번째 사용자 발화도 같은 history를 사용하여 이름 기억 여부를 확인합니다.
    print("[2턴]", manual_memory_turn(provider, history, "내 이름이 뭐라고 했지?"))
    # 누적된 사용자와 모델 메시지 수를 출력합니다.
    print(f"\n누적 메시지 수: {len(history)}")


def demo_inmemory(provider: str) -> None:
    """InMemorySaver와 동일 thread_id를 사용한 자동 기억을 확인합니다."""
    # 현재 기능 제목을 출력합니다.
    print_title("3. InMemorySaver 기억형 상담봇")
    # 선택한 모델로 메모리 에이전트를 한 번 생성합니다.
    agent = build_agent(provider)
    # 같은 thread_id로 첫 번째 대화를 실행합니다.
    answer1, _ = chat(agent, "내 이름은 민준이고 전자기기를 좋아해.", "user-A")
    # 첫 번째 답변을 출력합니다.
    print("[1턴]", answer1)
    # 같은 thread_id로 기억 확인 질문을 실행합니다.
    answer2, messages = chat(agent, "내 이름과 선호 카테고리를 말해줘.", "user-A")
    # 두 번째 답변을 출력합니다.
    print("[2턴]", answer2)
    # 체크포인터에 누적된 메시지 수를 출력합니다.
    print(f"\n누적 메시지 수: {len(messages)}")


def demo_session_isolation(provider: str) -> None:
    """thread_id가 다르면 같은 에이전트의 대화 기억도 분리되는지 확인합니다."""
    # 현재 기능 제목을 출력합니다.
    print_title("4. 같은 세션과 다른 세션 격리")
    # 하나의 에이전트 객체를 생성합니다.
    agent = build_agent(provider)
    # user-A 세션에 개인정보와 선호를 입력합니다.
    chat(agent, "내 이름은 민준이고 좋아하는 카테고리는 전자기기야.", "user-A")
    # user-B 세션에서 user-A의 정보를 질문합니다.
    answer_b, _ = chat(agent, "내 이름과 좋아하는 카테고리를 말해줘.", "user-B")
    # user-B 결과를 출력합니다.
    print("[user-B]", answer_b)
    # 다시 user-A 세션으로 돌아가 기존 정보를 질문합니다.
    answer_a, _ = chat(agent, "내 이름과 좋아하는 카테고리를 다시 말해줘.", "user-A")
    # user-A 결과를 출력합니다.
    print("[user-A 복귀]", answer_a)
    # 세션 분리의 핵심 관찰점을 출력합니다.
    print("\n관찰: 같은 에이전트라도 thread_id가 다르면 대화 상태가 분리됩니다.")


def demo_trim(provider: str) -> None:
    """긴 대화에서 최근 메시지만 남기는 트리밍을 확인합니다."""
    # 현재 기능 제목을 출력합니다.
    print_title("5. 긴 대화 트리밍")
    # 미리 준비한 긴 상담 메시지 목록을 생성합니다.
    messages = build_demo_messages()
    # 시스템 메시지와 최근 4개 대화 메시지만 남깁니다.
    trimmed = trim_recent(messages, keep=4)
    # 트리밍 전후 메시지 수를 출력합니다.
    print(f"원본 메시지 수: {len(messages)}")
    # 트리밍 후 메시지 수를 출력합니다.
    print(f"트리밍 메시지 수: {len(trimmed)}")
    # 남은 메시지를 순서대로 출력합니다.
    for index, message in enumerate(trimmed, start=1):
        # 메시지 클래스 이름과 텍스트를 함께 출력합니다.
        print(f"{index}. {type(message).__name__}: {message_to_text(message)}")


def demo_summary(provider: str) -> None:
    """오래된 대화를 요약 한 줄로 압축하는 방식을 확인합니다."""
    # 현재 기능 제목을 출력합니다.
    print_title("6. 긴 대화 요약 압축")
    # 미리 준비한 긴 상담 메시지 목록을 생성합니다.
    messages = build_demo_messages()
    # 오래된 대화를 요약하고 최근 4개 메시지는 그대로 유지합니다.
    summarized = summarize_old(provider, messages, keep_recent=4)
    # 요약 전후 메시지 수를 출력합니다.
    print(f"원본 메시지 수: {len(messages)}")
    # 요약 압축 후 메시지 수를 출력합니다.
    print(f"압축 메시지 수: {len(summarized)}")
    # 압축된 메시지를 순서대로 출력합니다.
    for index, message in enumerate(summarized, start=1):
        # 메시지 종류와 내용을 함께 출력합니다.
        print(f"{index}. {type(message).__name__}: {message_to_text(message)}")


def demo_data_consulting(provider: str) -> None:
    """data.zip의 고객·주문·상담 데이터를 사용한 기억형 상담을 실행합니다."""
    # 현재 기능 제목을 출력합니다.
    print_title("7. 데이터 기반 기억형 고객 상담")
    # 데이터에 존재하는 고객 ID 일부를 사용자에게 보여줍니다.
    sample_ids = list_sample_customer_ids()
    # 테스트 가능한 고객 ID 목록을 출력합니다.
    print("고객 ID 예시:", ", ".join(sample_ids) if sample_ids else "확인 불가")
    # 조회할 고객 ID를 입력받습니다.
    customer_id = input("조회할 고객 ID: ").strip()
    # 빈 값을 입력하면 첫 번째 예시 ID를 기본값으로 사용합니다.
    if not customer_id and sample_ids:
        customer_id = sample_ids[0]
    # 선택한 고객의 여러 데이터 파일 정보를 통합 조회합니다.
    context = load_customer_context(customer_id)
    # 조회된 데이터를 LLM 전달용 텍스트로 변환합니다.
    data_prompt = context_to_prompt(context)
    # 데이터 기반 상담을 위한 메모리 에이전트를 생성합니다.
    agent = build_agent(provider)
    # 고객 ID별 고유 thread_id를 구성합니다.
    thread_id = f"customer-{customer_id}"
    # 첫 턴에서 고객 데이터를 상담 맥락으로 전달합니다.
    first_question = input("첫 질문: ").strip() or "내 최근 주문과 상담 이력을 간단히 알려줘."
    # 데이터와 질문을 함께 전달하여 근거 기반 답변을 생성합니다.
    first_answer, _ = chat(
        agent,
        f"다음은 조회된 고객 데이터이다. 이 데이터만 근거로 답하라.\n\n{data_prompt}\n\n질문: {first_question}",
        thread_id,
    )
    # 첫 번째 상담 답변을 출력합니다.
    print("\n[상담원]", first_answer)
    # 두 번째 질문을 입력받아 같은 세션의 기억을 확인합니다.
    second_question = input("\n이어지는 질문: ").strip() or "방금 설명한 핵심 내용을 다시 한 문장으로 말해줘."
    # 두 번째 호출에는 고객 데이터를 다시 넣지 않고 thread_id 기억을 사용합니다.
    second_answer, _ = chat(agent, second_question, thread_id)
    # 두 번째 상담 답변을 출력합니다.
    print("\n[상담원]", second_answer)


def interactive_chat(provider: str) -> None:
    """사용자가 직접 thread_id를 지정하여 멀티턴 상담을 실행합니다."""
    # 현재 기능 제목을 출력합니다.
    print_title("8. 자유 대화 메모리 테스트")
    # 하나의 에이전트를 생성하여 여러 턴 동안 재사용합니다.
    agent = build_agent(provider)
    # 사용할 세션 ID를 입력받습니다.
    thread_id = input("thread_id 입력(기본: console-user): ").strip() or "console-user"
    # 종료 명령 안내를 출력합니다.
    print("대화를 입력하십시오. /exit 입력 시 종료합니다.")
    # 사용자가 종료할 때까지 대화 루프를 실행합니다.
    while True:
        # 사용자 메시지를 입력받습니다.
        user_text = input("\n사용자: ").strip()
        # 종료 명령이면 반복을 끝냅니다.
        if user_text.lower() in {"/exit", "exit", "종료"}:
            break
        # 빈 입력은 모델 호출 없이 다시 입력받습니다.
        if not user_text:
            continue
        # 동일한 thread_id로 메모리 대화를 실행합니다.
        answer, messages = chat(agent, user_text, thread_id)
        # 모델 답변을 출력합니다.
        print("상담원:", answer)
        # 현재 세션에 누적된 메시지 수를 출력합니다.
        print(f"[누적 메시지: {len(messages)}개]")


def run_provider_menu(provider: str) -> None:
    """선택한 공급자로 실행할 핵심 코드 메뉴를 반복 표시합니다."""
    # 메뉴 번호와 실행 함수를 연결한 딕셔너리를 정의합니다.
    actions = {
        "1": demo_stateless,
        "2": demo_manual_memory,
        "3": demo_inmemory,
        "4": demo_session_isolation,
        "5": demo_trim,
        "6": demo_summary,
        "7": demo_data_consulting,
        "8": interactive_chat,
    }
    # 사용자가 공급자 선택 화면으로 돌아갈 때까지 반복합니다.
    while True:
        # 현재 공급자 이름을 포함한 메뉴 제목을 출력합니다.
        print_title(f"Agent Memory 핵심 코드 실행 메뉴 - {provider.upper()}")
        # HTML 설명 정리 메뉴 없이 실행 가능한 핵심 기능만 출력합니다.
        print("1. Stateless 호출 비교")
        print("2. 수동 대화 기록 누적")
        print("3. InMemorySaver 기억형 상담봇")
        print("4. 같은 세션과 다른 세션 격리")
        print("5. 긴 대화 트리밍")
        print("6. 긴 대화 요약 압축")
        print("7. data.zip 기반 기억형 고객 상담")
        print("8. 자유 대화 메모리 테스트")
        print("0. LLM 공급자 선택으로 돌아가기")
        # 실행할 메뉴 번호를 입력받습니다.
        choice = input("선택: ").strip()
        # 0이면 현재 공급자 메뉴를 종료합니다.
        if choice == "0":
            return
        # 입력한 번호에 대응하는 함수를 찾습니다.
        action = actions.get(choice)
        # 등록되지 않은 번호이면 오류 메시지 후 메뉴를 다시 표시합니다.
        if action is None:
            print("0~8 사이의 메뉴 번호를 입력하십시오.")
            continue
        # API 오류와 데이터 오류가 전체 앱을 종료시키지 않도록 예외를 처리합니다.
        try:
            # 선택한 공급자 값을 기능 함수에 전달하여 실행합니다.
            action(provider)
        # 사용자가 Ctrl+C를 누르면 현재 기능만 중단합니다.
        except KeyboardInterrupt:
            print("\n현재 기능 실행을 중단했습니다.")
        # 그 밖의 오류는 유형과 메시지를 출력하여 해결에 도움을 줍니다.
        except Exception as error:
            print(f"\n[실행 오류] {type(error).__name__}: {error}")
        # 결과를 확인한 뒤 메뉴로 돌아갑니다.
        pause()


def main() -> None:
    """프로그램의 최상위 실행 흐름을 담당합니다."""
    # 프로그램 시작 안내를 출력합니다.
    print("Agent Memory 콘솔 앱을 시작합니다.")
    # 사용자가 종료를 선택할 때까지 공급자 선택을 반복합니다.
    while True:
        # OpenAI 또는 Gemini 공급자를 선택합니다.
        provider = choose_provider()
        # None이면 종료 안내를 출력하고 반복을 끝냅니다.
        if provider is None:
            print("프로그램을 종료합니다.")
            break
        # 선택한 공급자의 하위 기능 메뉴를 실행합니다.
        run_provider_menu(provider)


# 이 파일을 직접 실행할 때만 main 함수를 호출합니다.
if __name__ == "__main__":
    # 프로그램의 진입점 함수를 실행합니다.
    main()
