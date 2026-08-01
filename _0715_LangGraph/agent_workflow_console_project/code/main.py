# -*- coding: utf-8 -*-
"""OpenAI/Gemini와 LangGraph, PyTorch를 확인하는 콘솔 메뉴 프로그램입니다."""

# CSV 파일을 딕셔너리 형태로 읽기 위해 csv 모듈을 가져옵니다.
import csv

# 타입 힌트에서 Callable을 사용하기 위해 가져옵니다.
from collections.abc import Callable

# 공통 환경 점검 함수와 데이터 폴더 경로를 가져옵니다.
from common import DATA, print_environment_status

# PyTorch 실습 실행 함수를 가져옵니다.
from torch_demo import run_torch_demo

# 워크플로우 생성 함수와 개별 규칙 노드를 가져옵니다.
from workflow import (
    assign_node,
    build_conditional_workflow,
    build_linear_workflow,
    priority_node,
)


# 프로그램 실행 중 현재 선택된 LLM 공급자를 저장합니다.
CURRENT_PROVIDER = "gemini"


def print_title(title: str) -> None:
    """각 실습 화면의 제목을 일정한 형식으로 출력합니다."""

    # 제목 위쪽 구분선을 출력합니다.
    print("\n" + "=" * 78)

    # 전달받은 제목을 출력합니다.
    print(title)

    # 제목 아래쪽 구분선을 출력합니다.
    print("=" * 78)


def choose_provider() -> None:
    """Gemini 또는 OpenAI 중 이후 실습에서 사용할 공급자를 선택합니다."""

    # 모듈 수준 공급자 변수를 변경할 것임을 파이썬에 알립니다.
    global CURRENT_PROVIDER

    # 공급자 선택 화면 제목을 출력합니다.
    print_title("LLM 공급자 선택")

    # 사용 가능한 첫 번째 공급자를 표시합니다.
    print("1. Gemini API")

    # 사용 가능한 두 번째 공급자를 표시합니다.
    print("2. OpenAI API")

    # 사용자의 메뉴 입력을 읽고 앞뒤 공백을 제거합니다.
    selected = input("선택 번호 [현재: " + CURRENT_PROVIDER + "]: ").strip()

    # 1번을 입력하면 Gemini를 현재 공급자로 지정합니다.
    if selected == "1":
        CURRENT_PROVIDER = "gemini"
    # 2번을 입력하면 OpenAI를 현재 공급자로 지정합니다.
    elif selected == "2":
        CURRENT_PROVIDER = "openai"
    # 빈 입력은 현재 값을 유지하고 다른 값은 안내 메시지만 출력합니다.
    elif selected:
        print("지원하지 않는 번호입니다. 기존 공급자를 유지합니다.")

    # 최종 선택된 공급자를 출력합니다.
    print("현재 공급자:", CURRENT_PROVIDER)


def run_rule_nodes_demo() -> None:
    """LLM 호출 없이 우선순위와 담당팀 규칙 노드를 각각 실행합니다."""

    # 개별 노드 실행 화면 제목을 출력합니다.
    print_title("규칙 기반 노드 개별 실행")

    # 사용자가 티켓 내용을 입력하도록 요청합니다.
    content = input("티켓 내용: ").strip() or "환불하고 싶습니다."

    # 분류 결과는 이번 실습에서 사용자가 직접 선택하도록 안내합니다.
    category = input("분류 카테고리 [기본: 환불]: ").strip() or "환불"

    # 두 규칙 노드가 읽을 초기 상태 딕셔너리를 만듭니다.
    state = {"content": content, "category": category}

    # 우선순위 노드를 독립적으로 호출합니다.
    priority_update = priority_node(state)

    # 우선순위 결과를 기존 상태에 합칩니다.
    state.update(priority_update)

    # 담당팀 배정 노드를 독립적으로 호출합니다.
    team_update = assign_node(state)

    # 팀 배정 결과를 기존 상태에 합칩니다.
    state.update(team_update)

    # 각 노드가 채운 최종 상태를 출력합니다.
    print("실행 결과:", state)


def run_single_linear() -> None:
    """선택한 LLM으로 한 건의 티켓을 선형 StateGraph에서 처리합니다."""

    # 선형 워크플로우 화면 제목을 출력합니다.
    print_title(f"선형 StateGraph 단일 처리 - {CURRENT_PROVIDER}")

    # 사용자가 처리할 티켓 내용을 입력합니다.
    content = input("티켓 내용: ").strip() or "결제가 안 돼요. 계속 오류가 납니다."

    # 현재 공급자에 맞는 실행 가능한 선형 그래프를 생성합니다.
    workflow = build_linear_workflow(CURRENT_PROVIDER)

    # content만 가진 초기 상태를 워크플로우에 전달합니다.
    result = workflow.invoke({"content": content})

    # 분류, 우선순위, 담당팀이 누적된 최종 상태를 출력합니다.
    print("최종 상태:", result)


def load_tickets() -> list[dict[str, str]]:
    """data/support_tickets.csv 파일을 읽어 티켓 딕셔너리 목록으로 반환합니다."""

    # 공통 DATA 경로 아래의 CSV 파일 경로를 만듭니다.
    csv_path = DATA / "support_tickets.csv"

    # 엑셀에서 저장된 CSV의 BOM까지 안전하게 처리하도록 utf-8-sig로 파일을 엽니다.
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        # 첫 행의 열 이름을 키로 사용하는 DictReader를 생성합니다.
        reader = csv.DictReader(file)

        # 반복 가능한 reader의 모든 행을 리스트로 변환하여 반환합니다.
        return list(reader)


def run_batch_linear() -> None:
    """CSV의 모든 티켓을 알림 조건부 워크플로우로 일괄 처리합니다."""

    # 일괄 처리 화면 제목을 출력합니다.
    print_title(f"CSV 알림 조건부 워크플로우 일괄 처리 - {CURRENT_PROVIDER}")

    # 현재 공급자를 사용하는 조건부 그래프를 한 번만 생성합니다.
    workflow = build_conditional_workflow(CURRENT_PROVIDER)

    # CSV에서 실습용 티켓 목록을 읽습니다.
    tickets = load_tickets()

    # 결과 열의 제목을 일정한 너비로 출력합니다.
    print(f"{'티켓':<8}{'분류':<10}{'우선순위':<10}{'알림':<12}{'담당팀':<14}{'상태'}")

    # 표의 제목과 데이터를 구분하는 선을 출력합니다.
    print("-" * 78)

    # CSV에서 읽은 각 티켓을 하나씩 처리합니다.
    for ticket in tickets:
        # 현재 티켓 내용을 초기 상태로 전달하여 워크플로우를 실행합니다.
        result = workflow.invoke({"content": ticket["content"]})

        # 오류가 없으면 정상, 있으면 오류 메시지를 상태 열에 표시합니다.
        status = result.get("error") or "정상"

        # 한 티켓의 주요 결과를 한 줄로 정렬하여 출력합니다.
        print(
            f"{ticket['ticket_id']:<8}"
            f"{result.get('category', ''):<10}"
            f"{result.get('priority', ''):<10}"
            f"{result.get('alert', ''):<12}"
            f"{result.get('team', ''):<14}"
            f"{status}"
        )


def run_conditional() -> None:
    """긴급과 일반 티켓이 다른 노드로 이동하는 조건부 그래프를 실행합니다."""

    # 조건부 분기 화면 제목을 출력합니다.
    print_title(f"조건부 분기 워크플로우 - {CURRENT_PROVIDER}")

    # 현재 공급자를 사용하는 조건부 그래프를 생성합니다.
    workflow = build_conditional_workflow(CURRENT_PROVIDER)

    # 사용자가 직접 입력하지 않으면 긴급 경로 예제를 사용합니다.
    content = input("티켓 내용: ").strip() or "배송이 일주일째 안 와요."

    # 초기 상태를 전달하여 분류와 우선순위 이후 분기 경로를 실행합니다.
    result = workflow.invoke({"content": content})

    # 최종 상태 전체를 출력하여 긴급 티켓의 alert 값을 확인합니다.
    print("최종 상태:", result)


def run_failure_demo() -> None:
    """분류 노드 예외가 오류 상태와 검토필요 팀으로 이어지는지 확인합니다."""

    # 실패 처리 실습 화면 제목을 출력합니다.
    print_title("노드 실패 처리와 상태 검증 - 강제 분류 예외")

    class FailureDemoLLM:
        """특정 입력에서 의도적으로 예외를 던지는 검증 전용 가짜 모델입니다."""

        def invoke(self, messages):
            # 마지막 사용자 메시지에 강제예외 표시가 있으면 분류 노드 내부에서 실패시킵니다.
            content = str(messages[-1].content)
            if "강제예외" in content:
                raise RuntimeError("실습용 classify 강제 예외")

            # 정상 샘플은 외부 API 없이 회원 카테고리를 반환합니다.
            return "회원"

    # API 키 없이 성공과 실패를 반복 검증할 수 있는 선형 그래프를 생성합니다.
    workflow = build_linear_workflow(CURRENT_PROVIDER, llm=FailureDemoLLM())

    # 정상 입력과 분류 예외 입력을 함께 준비합니다.
    samples = [
        ("NORMAL", "회원 정보 변경 방법을 알려주세요."),
        ("CLASSIFY_ERROR", "강제예외를 발생시켜 주세요."),
    ]

    # 두 입력을 차례로 실행하여 오류 티켓만 검토필요 팀이 되는지 확인합니다.
    for ticket_id, content in samples:
        # 현재 샘플을 워크플로우에 전달합니다.
        result = workflow.invoke({"content": content})

        # error 필드가 비어 있으면 정상으로 표시합니다.
        status = result.get("error") or "정상"

        # 보정된 분류, 우선순위, 담당팀, 오류 기록을 출력합니다.
        print(
            ticket_id,
            result.get("category"),
            result.get("priority"),
            result.get("team"),
            status,
        )


def run_provider_comparison() -> None:
    """같은 티켓을 Gemini와 OpenAI에 각각 전달하여 분류 결과를 비교합니다."""

    # 두 공급자 비교 화면 제목을 출력합니다.
    print_title("Gemini API와 OpenAI API 결과 비교")

    # 두 모델에 동일하게 전달할 티켓 내용을 입력합니다.
    content = input("티켓 내용: ").strip() or "앱이 자꾸 튕기고 로그인이 풀립니다."

    # 비교할 공급자 이름을 고정된 순서로 순회합니다.
    for provider in ("gemini", "openai"):
        try:
            # 현재 비교 대상 공급자의 선형 그래프를 생성합니다.
            workflow = build_linear_workflow(provider)

            # 동일한 입력으로 워크플로우를 실행합니다.
            result = workflow.invoke({"content": content})

            # 공급자 이름과 주요 결과를 출력합니다.
            print(provider, "→", result)
        except SystemExit as exc:
            # 해당 공급자의 API 키가 없더라도 다른 공급자 비교는 계속합니다.
            print(provider, "→ 설정 오류:", exc)


def pause() -> None:
    """사용자가 결과를 읽은 뒤 메뉴로 돌아가도록 Enter 입력을 기다립니다."""

    # 콘솔 출력이 바로 사라지지 않도록 Enter 입력을 받습니다.
    input("\nEnter를 누르면 메뉴로 돌아갑니다...")


def print_menu() -> None:
    """실행 가능한 실습 기능만 메뉴로 출력합니다."""

    # 프로그램 이름과 현재 선택된 공급자를 출력합니다.
    print_title(f"Agent Workflow 콘솔 실습 앱 (현재 LLM: {CURRENT_PROVIDER})")

    # 환경변수와 공통 경로 확인 기능을 표시합니다.
    print("1. 공통 환경 및 API 키 로드 상태 확인")

    # 이후 LLM 실습에서 사용할 공급자 변경 기능을 표시합니다.
    print("2. LLM 공급자 선택 (Gemini / OpenAI)")

    # PyTorch 텐서 연산 실습을 표시합니다.
    print("3. PyTorch 기반 티켓 우선순위 점수 확인")

    # LLM 없이 규칙 노드만 개별 실행하는 기능을 표시합니다.
    print("4. 규칙 기반 노드 개별 실행")

    # 한 건의 티켓을 선형 그래프로 실행하는 기능을 표시합니다.
    print("5. StateGraph 선형 워크플로우 단일 처리")

    # CSV 전체를 선형 그래프로 일괄 처리하는 기능을 표시합니다.
    print("6. CSV 티켓 일괄 처리")

    # 우선순위에 따라 실행 노드가 달라지는 기능을 표시합니다.
    print("7. add_conditional_edges 조건부 분기")

    # 강제 분류 예외와 검토필요 최종 배정 기능을 표시합니다.
    print("8. 노드 예외 처리와 검토필요 배정 검증")

    # Gemini와 OpenAI의 동일 입력 결과 비교 기능을 표시합니다.
    print("9. Gemini / OpenAI 결과 비교")

    # 프로그램 종료 기능을 표시합니다.
    print("0. 종료")


def main() -> None:
    """사용자가 종료할 때까지 콘솔 메뉴를 반복 실행합니다."""

    # 메뉴 번호와 실행 함수의 연결 관계를 딕셔너리로 정의합니다.
    menu_actions: dict[str, Callable[[], None]] = {
        "1": print_environment_status,
        "2": choose_provider,
        "3": run_torch_demo,
        "4": run_rule_nodes_demo,
        "5": run_single_linear,
        "6": run_batch_linear,
        "7": run_conditional,
        "8": run_failure_demo,
        "9": run_provider_comparison,
    }

    # 사용자가 0번을 선택하기 전까지 메뉴를 계속 표시합니다.
    while True:
        # 현재 메뉴 항목을 화면에 출력합니다.
        print_menu()

        # 사용자가 선택한 번호를 문자열로 읽습니다.
        selected = input("메뉴 번호를 선택하세요: ").strip()

        # 0번이면 반복문을 종료하여 프로그램을 끝냅니다.
        if selected == "0":
            print("프로그램을 종료합니다.")
            break

        # 입력한 번호와 연결된 실행 함수를 딕셔너리에서 찾습니다.
        action = menu_actions.get(selected)

        # 존재하지 않는 번호라면 오류 안내 후 메뉴를 다시 표시합니다.
        if action is None:
            print("지원하지 않는 메뉴 번호입니다.")
            pause()
            continue

        try:
            # 선택한 메뉴의 실제 실습 함수를 실행합니다.
            action()
        except SystemExit as exc:
            # API 키 미설정 같은 설정 오류를 전체 프로그램 종료 없이 안내합니다.
            print(exc)
        except FileNotFoundError as exc:
            # 필요한 CSV가 없을 때 어떤 파일이 누락됐는지 출력합니다.
            print("필요한 파일을 찾지 못했습니다:", exc)
        except Exception as exc:
            # 예상하지 못한 오류도 메뉴 루프가 종료되지 않도록 포착합니다.
            print(f"[실행 오류] {type(exc).__name__}: {exc}")

        # 실행 결과를 확인한 뒤 메뉴로 돌아갈 수 있도록 대기합니다.
        pause()


# 이 파일을 직접 실행할 때만 main 함수를 호출합니다.
if __name__ == "__main__":
    # PyCharm에서 code/main.py를 실행하면 콘솔 메뉴가 시작됩니다.
    main()
