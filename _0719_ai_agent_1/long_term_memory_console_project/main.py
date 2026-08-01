# -*- coding: utf-8 -*-
"""PyCharm에서 바로 실행하는 OpenAI/Gemini 선택형 장기 기억 콘솔 앱입니다."""

# json 모듈은 프로필 딕셔너리를 보기 좋은 JSON 문자열로 출력할 때 사용합니다.
import json
# sys 모듈은 프로젝트 루트를 파이썬 모듈 검색 경로에 추가할 때 사용합니다.
import sys
# Path는 실행 위치와 관계없이 프로젝트의 절대 경로를 계산합니다.
from pathlib import Path

# 현재 main.py가 들어 있는 디렉터리를 프로젝트 루트로 계산합니다.
PROJECT_ROOT = Path(__file__).resolve().parent
# PyCharm의 Working directory 설정이 달라도 code 패키지를 찾을 수 있는지 확인합니다.
if str(PROJECT_ROOT) not in sys.path:
    # 프로젝트 루트를 모듈 검색 경로의 맨 앞에 추가합니다.
    sys.path.insert(0, str(PROJECT_ROOT))

# data.zip의 고객 관련 데이터를 통합 조회하는 기존 공통 서비스를 가져옵니다.
from code.data_service import context_to_prompt, list_sample_customer_ids, load_customer_context
# 단기·장기 기억 에이전트 생성 함수와 대화 실행 함수를 가져옵니다.
from code.long_term_agent import build_long_term_agent, say
# JSON·SQLite 저장소의 직접 조회·갱신 및 초기화 함수를 가져옵니다.
from code.long_term_store import (
    JSON_STORE,
    SQLITE_DB,
    init_sqlite_from_json,
    read_json_profile,
    read_sqlite_profile,
    reset_json_store,
    write_json_profile,
    write_sqlite_profile,
)


def print_title(title: str) -> None:
    """기능별 제목을 동일한 형식으로 출력합니다."""
    # 이전 출력과 구분하기 위한 빈 줄과 위쪽 구분선을 출력합니다.
    print("\n" + "=" * 76)
    # 전달받은 제목 문자열을 출력합니다.
    print(title)
    # 제목 아래 구분선을 출력합니다.
    print("=" * 76)


def pause() -> None:
    """사용자가 실행 결과를 읽은 뒤 메뉴로 돌아가도록 대기합니다."""
    # Enter 키가 입력될 때까지 프로그램 실행을 잠시 멈춥니다.
    input("\nEnter 키를 누르면 메뉴로 돌아갑니다.")


def choose_provider() -> str | None:
    """OpenAI 또는 Gemini 중 사용할 LLM 공급자를 선택합니다."""
    # 올바른 선택이 입력될 때까지 공급자 메뉴를 반복합니다.
    while True:
        # 공급자 선택 화면 제목을 출력합니다.
        print_title("LLM 공급자 선택")
        # OpenAI 메뉴를 출력합니다.
        print("1. OpenAI")
        # Gemini 메뉴를 출력합니다.
        print("2. Gemini")
        # 종료 메뉴를 출력합니다.
        print("0. 종료")
        # 사용자의 입력에서 앞뒤 공백을 제거합니다.
        choice = input("선택: ").strip()
        # 1이면 common.py가 이해하는 openai 문자열을 반환합니다.
        if choice == "1":
            # OpenAI 선택값을 반환합니다.
            return "openai"
        # 2이면 common.py가 이해하는 gemini 문자열을 반환합니다.
        if choice == "2":
            # Gemini 선택값을 반환합니다.
            return "gemini"
        # 0이면 프로그램 종료를 뜻하는 None을 반환합니다.
        if choice == "0":
            # 상위 반복문이 종료할 수 있도록 None을 반환합니다.
            return None
        # 잘못된 번호 입력을 안내합니다.
        print("1, 2, 0 중 하나를 입력하십시오.")


def demo_memory_difference(provider: str) -> None:
    """단기 기억과 장기 기억이 저장되는 위치와 수명을 실행으로 비교합니다."""
    # 현재 기능 제목을 출력합니다.
    print_title("1. 단기 기억과 장기 기억 실행 비교")
    # 단기·장기 기억을 모두 가진 에이전트를 생성합니다.
    agent = build_long_term_agent(provider, backend="json")
    # 첫 세션에서 단기 정보만 말하고 저장 도구를 요청하지 않습니다.
    first_answer, _ = say(agent, "이번 대화에서만 내 별명을 번개라고 기억해 줘.", "short-session")
    # 첫 번째 답변을 출력합니다.
    print("[현재 세션]", first_answer)
    # 같은 세션에서 단기 기억을 확인합니다.
    same_answer, _ = say(agent, "방금 말한 내 별명이 뭐였지?", "short-session")
    # 같은 세션의 기억 결과를 출력합니다.
    print("[같은 세션]", same_answer)
    # 새 에이전트를 만들어 단기 메모리가 사라진 재시작 상태를 시뮬레이션합니다.
    restarted_agent = build_long_term_agent(provider, backend="json")
    # 다른 세션에서 별명을 질문하여 단기 기억이 이어지지 않음을 확인합니다.
    new_answer, _ = say(restarted_agent, "방금 말한 내 별명이 뭐였지?", "new-session")
    # 새 세션 결과를 출력합니다.
    print("[새 에이전트/새 세션]", new_answer)
    # 핵심 관찰점을 출력합니다.
    print("\n관찰: InMemorySaver의 단기 기억은 에이전트를 새로 만들면 사라집니다.")


def demo_json_tools(provider: str) -> None:
    """JSON 프로필 읽기·쓰기 핵심 코드를 LLM 없이 직접 실행합니다."""
    # 현재 기능 제목을 출력합니다.
    print_title("2. JSON 프로필 읽기·쓰기 도구 직접 실행")
    # 테스트할 고객 ID를 입력받고 빈 입력이면 C0001을 사용합니다.
    customer_id = input("고객 ID(기본 C0001): ").strip() or "C0001"
    # 변경할 필드를 입력받고 빈 입력이면 관심사를 사용합니다.
    field = input("변경 필드(기본 관심사): ").strip() or "관심사"
    # 저장할 값을 입력받고 빈 입력이면 캠핑 용품을 사용합니다.
    value = input("저장 값(기본 캠핑 용품): ").strip() or "캠핑 용품"
    # 변경 전 프로필을 JSON 저장소에서 조회합니다.
    before = read_json_profile(customer_id)
    # 변경 전 값을 보기 좋은 JSON으로 출력합니다.
    print("\n[변경 전]", json.dumps(before, ensure_ascii=False, indent=2))
    # 해당 고객의 지정 필드를 파일에 영속 저장합니다.
    result = write_json_profile(customer_id, field, value)
    # 저장 결과 메시지를 출력합니다.
    print("\n[저장 결과]", result)
    # 파일을 다시 읽어 실제 반영된 프로필을 조회합니다.
    after = read_json_profile(customer_id)
    # 변경 후 값을 출력하여 디스크 저장 여부를 검증합니다.
    print("\n[변경 후]", json.dumps(after, ensure_ascii=False, indent=2))
    # 실제 쓰기 대상 파일 경로를 출력합니다.
    print(f"\n저장 파일: {JSON_STORE}")


def demo_agent_json_memory(provider: str) -> None:
    """에이전트가 JSON 장기 기억 도구를 스스로 호출하는 과정을 실행합니다."""
    # 현재 기능 제목을 출력합니다.
    print_title("3. JSON 장기 기억 도구 사용 에이전트")
    # JSON 도구를 연결한 에이전트를 생성합니다.
    agent = build_long_term_agent(provider, backend="json")
    # 저장할 고객 ID를 입력받고 기본값을 지정합니다.
    customer_id = input("고객 ID(기본 C0001): ").strip() or "C0001"
    # 저장할 장기 정보를 입력받습니다.
    memory_text = input("기억시킬 정보: ").strip() or "선크림 알레르기가 있으니 비고에 저장해 주세요."
    # 고객 ID와 저장 요청을 포함한 메시지를 전달하여 update_profile 도구 호출을 유도합니다.
    answer, _ = say(agent, f"저는 {customer_id} 고객입니다. {memory_text}", "json-save-session")
    # 에이전트의 최종 답변을 출력합니다.
    print("\n[상담원]", answer)
    # 저장 결과를 파일에서 직접 다시 읽어 검증합니다.
    print("\n[파일 검증]", json.dumps(read_json_profile(customer_id), ensure_ascii=False, indent=2))


def demo_new_session_memory(provider: str) -> None:
    """새 에이전트와 새 thread_id에서도 JSON 장기 기억이 유지되는지 확인합니다."""
    # 현재 기능 제목을 출력합니다.
    print_title("4. 새 세션에서도 유지되는 장기 기억")
    # 조회할 고객 ID를 입력받습니다.
    customer_id = input("고객 ID(기본 C0001): ").strip() or "C0001"
    # 첫 번째 에이전트를 생성합니다.
    first_agent = build_long_term_agent(provider, backend="json")
    # 첫 에이전트가 비고 필드에 장기 정보를 저장하도록 요청합니다.
    save_answer, _ = say(
        first_agent,
        f"저는 {customer_id} 고객입니다. 비고에 '향이 강한 제품은 피함'을 기억해 저장해 주세요.",
        "session-before-restart",
    )
    # 저장 단계의 답변을 출력합니다.
    print("[1단계 저장]", save_answer)
    # 완전히 새 에이전트를 생성하여 단기 기억을 초기화합니다.
    second_agent = build_long_term_agent(provider, backend="json")
    # 다른 thread_id에서 프로필을 조회해 개인화 응대를 요청합니다.
    recall_answer, _ = say(
        second_agent,
        f"{customer_id} 고객에게 제품을 추천하기 전에 프로필을 조회하고 주의점을 말해 주세요.",
        "session-after-restart",
    )
    # 새 세션의 조회 결과를 출력합니다.
    print("\n[2단계 새 에이전트 조회]", recall_answer)
    # 디스크 파일이 장기 기억의 근거임을 출력합니다.
    print(f"\n장기 기억 근거 파일: {JSON_STORE}")


def demo_sqlite(provider: str) -> None:
    """JSON 원본을 SQLite로 이관하고 행 단위 조회·갱신을 실행합니다."""
    # 현재 기능 제목을 출력합니다.
    print_title("5. SQLite 장기 기억 이관·조회·갱신")
    # 기존 DB를 유지할지 초기화할지 사용자에게 선택받습니다.
    reset_choice = input("SQLite를 원본 JSON으로 초기화할까요? (y/N): ").strip().lower()
    # y 입력일 때만 기존 DB를 삭제하고 원본에서 다시 이관합니다.
    init_sqlite_from_json(force_reset=reset_choice == "y")
    # 조회할 고객 ID를 입력받습니다.
    customer_id = input("고객 ID(기본 C0001): ").strip() or "C0001"
    # SQLite에서 변경 전 고객 한 행만 조회합니다.
    print("\n[변경 전]", json.dumps(read_sqlite_profile(customer_id), ensure_ascii=False, indent=2))
    # 관심사 필드를 SQLite에서 안전한 파라미터 쿼리로 갱신합니다.
    print("\n[갱신]", write_sqlite_profile(customer_id, "관심사", "AI 기기, 스마트홈"))
    # 갱신 후 같은 고객 한 행을 다시 조회합니다.
    print("\n[변경 후]", json.dumps(read_sqlite_profile(customer_id), ensure_ascii=False, indent=2))
    # 실제 SQLite 파일 경로를 출력합니다.
    print(f"\nSQLite 파일: {SQLITE_DB}")


def demo_sqlite_agent(provider: str) -> None:
    """SQLite 도구 인터페이스를 사용하는 장기 기억 에이전트를 실행합니다."""
    # 현재 기능 제목을 출력합니다.
    print_title("6. SQLite 장기 기억 에이전트")
    # SQLite 테이블과 초기 데이터를 준비합니다.
    init_sqlite_from_json()
    # SQLite 읽기·쓰기 도구를 연결한 에이전트를 생성합니다.
    agent = build_long_term_agent(provider, backend="sqlite")
    # 고객 ID를 입력받습니다.
    customer_id = input("고객 ID(기본 C0002): ").strip() or "C0002"
    # SQLite 프로필을 먼저 조회하도록 명시한 개인화 질문을 구성합니다.
    question = input("질문: ").strip() or "내 프로필을 확인하고 나에게 맞는 제품 추천 기준을 말해 줘."
    # 고객 ID를 포함해 에이전트를 호출합니다.
    answer, _ = say(agent, f"저는 {customer_id} 고객입니다. {question}", f"sqlite-{customer_id}")
    # 에이전트의 최종 답변을 출력합니다.
    print("\n[상담원]", answer)


def demo_data_consulting(provider: str) -> None:
    """data.zip의 고객·주문·상담 데이터와 장기 프로필을 함께 사용합니다."""
    # 현재 기능 제목을 출력합니다.
    print_title("7. data.zip 기반 개인화 고객 상담")
    # 조회 가능한 고객 ID 예시를 가져옵니다.
    sample_ids = list_sample_customer_ids()
    # 사용자에게 고객 ID 예시를 출력합니다.
    print("고객 ID 예시:", ", ".join(sample_ids) if sample_ids else "확인 불가")
    # 조회할 고객 ID를 입력받고 비어 있으면 첫 예시를 사용합니다.
    customer_id = input("고객 ID: ").strip() or (sample_ids[0] if sample_ids else "C0001")
    # customers.csv, orders.csv, cs_inquiries.csv, user_profiles.json 정보를 통합 조회합니다.
    customer_context = load_customer_context(customer_id)
    # 통합 데이터를 LLM이 읽을 수 있는 근거 텍스트로 변환합니다.
    context_text = context_to_prompt(customer_context)
    # JSON 장기 기억 도구를 포함한 에이전트를 생성합니다.
    agent = build_long_term_agent(provider, backend="json")
    # 사용자 질문을 입력받습니다.
    question = input("질문: ").strip() or "최근 주문과 프로필을 고려해 주의할 점을 알려줘."
    # 조회된 데이터만 근거로 사용하고 프로필 도구도 확인하도록 프롬프트를 전달합니다.
    answer, _ = say(
        agent,
        f"고객 ID는 {customer_id}이다. 먼저 프로필 도구를 조회하라. "
        f"다음 데이터만 추가 근거로 사용하라.\n\n{context_text}\n\n질문: {question}",
        f"data-{customer_id}",
    )
    # 데이터 기반 개인화 답변을 출력합니다.
    print("\n[상담원]", answer)


def practice_answer_one(provider: str) -> None:
    """실습문제 1의 프로필 읽기·쓰기 해답을 실행합니다."""
    # 현재 기능 제목을 출력합니다.
    print_title("8-1. 실습문제 해답 1 - 프로필 읽기·쓰기")
    # 실습문제의 지정 고객과 값을 변수로 정의합니다.
    customer_id = "C0001"
    # 실습문제에서 요구한 선호 카테고리 값을 저장합니다.
    result = write_json_profile(customer_id, "선호카테고리", "가전")
    # 저장 함수의 결과를 출력합니다.
    print(result)
    # 파일을 다시 읽어 실제 저장된 값을 검증합니다.
    stored_value = read_json_profile(customer_id).get("선호카테고리")
    # 검증 값을 출력합니다.
    print("파일 확인:", stored_value)
    # 기대한 목록 값과 일치하는지 불리언 결과를 출력합니다.
    print("성공 여부:", stored_value == ["가전"])


def practice_answer_two(provider: str) -> None:
    """실습문제 2의 프로그램 재실행 장기 기억 해답을 한 메뉴에서 단계별 실행합니다."""
    # 현재 기능 제목을 출력합니다.
    print_title("8-2. 실습문제 해답 2 - 세션 종료 후에도 기억")
    # 1차 실행을 가정하여 관심사를 파일에 저장합니다.
    print("[1차 실행]", write_json_profile("C0001", "관심사", "캠핑 용품"))
    # 새 프로세스의 load 동작을 가정해 파일을 다시 읽습니다.
    reloaded_profile = read_json_profile("C0001")
    # 2차 실행에서 읽은 관심사 값을 출력합니다.
    print("[2차 실행] 재시작 후 읽은 관심사:", reloaded_profile.get("관심사"))
    # 기대 값과 일치하는지 확인합니다.
    print("성공 여부:", reloaded_profile.get("관심사") == "캠핑 용품")


def reset_stores(provider: str) -> None:
    """실습 중 변경된 JSON과 SQLite 저장소를 원본 상태로 복구합니다."""
    # 현재 기능 제목을 출력합니다.
    print_title("9. 장기 기억 저장소 초기화")
    # 사용자에게 실제 초기화 여부를 확인합니다.
    confirm = input("user_profiles_rw.json과 profiles.db를 초기화할까요? (y/N): ").strip().lower()
    # y가 아니면 아무것도 변경하지 않고 종료합니다.
    if confirm != "y":
        # 취소 메시지를 출력합니다.
        print("초기화를 취소했습니다.")
        # 함수 실행을 종료합니다.
        return
    # JSON 복사본을 data.zip 원본 상태로 되돌립니다.
    reset_json_store()
    # SQLite DB도 삭제 후 원본 JSON에서 다시 이관합니다.
    init_sqlite_from_json(force_reset=True)
    # 완료 메시지를 출력합니다.
    print("JSON 및 SQLite 장기 기억 저장소를 초기화했습니다.")


def run_provider_menu(provider: str) -> None:
    """선택한 LLM으로 핵심 코드와 실습 해답 실행 메뉴를 반복 표시합니다."""
    # 메뉴 번호와 실행 함수를 연결합니다.
    actions = {
        "1": demo_memory_difference,
        "2": demo_json_tools,
        "3": demo_agent_json_memory,
        "4": demo_new_session_memory,
        "5": demo_sqlite,
        "6": demo_sqlite_agent,
        "7": demo_data_consulting,
        "8-1": practice_answer_one,
        "8-2": practice_answer_two,
        "9": reset_stores,
    }
    # 사용자가 상위 공급자 메뉴로 돌아갈 때까지 반복합니다.
    while True:
        # 현재 공급자를 포함한 메뉴 제목을 출력합니다.
        print_title(f"Long-Term Memory 핵심 코드 실행 메뉴 - {provider.upper()}")
        # HTML 설명 정리 메뉴는 제외하고 실행 가능한 핵심 코드만 표시합니다.
        print("1. 단기 기억과 장기 기억 실행 비교")
        print("2. JSON 프로필 읽기·쓰기 도구 직접 실행")
        print("3. JSON 장기 기억 도구 사용 에이전트")
        print("4. 새 세션에서도 유지되는 장기 기억")
        print("5. SQLite 장기 기억 이관·조회·갱신")
        print("6. SQLite 장기 기억 에이전트")
        print("7. data.zip 기반 개인화 고객 상담")
        print("8-1. 실습문제 해답 1 실행")
        print("8-2. 실습문제 해답 2 실행")
        print("9. 장기 기억 저장소 초기화")
        print("0. LLM 공급자 선택으로 돌아가기")
        # 메뉴 번호를 입력받습니다.
        choice = input("선택: ").strip()
        # 0이면 현재 메뉴를 종료합니다.
        if choice == "0":
            # 공급자 선택 메뉴로 돌아갑니다.
            return
        # 입력 번호에 연결된 실행 함수를 찾습니다.
        action = actions.get(choice)
        # 등록되지 않은 입력이면 다시 선택하도록 안내합니다.
        if action is None:
            # 유효한 번호 범위를 안내합니다.
            print("표시된 메뉴 번호 중 하나를 입력하십시오.")
            # 다음 반복으로 이동합니다.
            continue
        # 기능 하나의 오류가 전체 앱 종료로 이어지지 않도록 예외를 처리합니다.
        try:
            # 선택된 기능에 현재 LLM 공급자를 전달해 실행합니다.
            action(provider)
        # Ctrl+C 입력은 현재 기능만 중단합니다.
        except KeyboardInterrupt:
            # 중단 안내를 출력합니다.
            print("\n현재 기능 실행을 중단했습니다.")
        # 나머지 오류는 오류 유형과 내용을 출력합니다.
        except Exception as error:
            # API 키, 네트워크, 데이터 오류를 확인할 수 있게 상세 메시지를 표시합니다.
            print(f"\n[실행 오류] {type(error).__name__}: {error}")
        # 실행 결과 확인 후 메뉴로 돌아갑니다.
        pause()


def main() -> None:
    """프로그램의 최상위 실행 흐름을 담당합니다."""
    # 앱 시작 안내를 출력합니다.
    print("Long-Term Memory 콘솔 앱을 시작합니다.")
    # 사용자가 종료할 때까지 공급자 선택을 반복합니다.
    while True:
        # OpenAI 또는 Gemini 공급자를 선택합니다.
        provider = choose_provider()
        # None이면 종료를 선택한 것입니다.
        if provider is None:
            # 종료 메시지를 출력합니다.
            print("프로그램을 종료합니다.")
            # 최상위 반복문을 종료합니다.
            break
        # 선택한 공급자의 핵심 코드 메뉴를 실행합니다.
        run_provider_menu(provider)


# 이 파일을 직접 실행할 때만 main 함수를 호출합니다.
if __name__ == "__main__":
    # 콘솔 앱의 진입점 함수를 실행합니다.
    main()
