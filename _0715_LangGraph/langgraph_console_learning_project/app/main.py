# -*- coding: utf-8 -*-
"""LangGraph 핵심 개념을 메뉴별로 실행하는 콘솔 애플리케이션입니다."""

# 각 실습 모듈을 app 패키지에서 가져옵니다.
from app import (
    basic_graph,
    checkpoint_graph,
    conditional_graph,
    error_graph,
    loop_graph,
    messages_graph,
    reducer_graph,
)

# 공통 콘솔 출력 함수를 가져옵니다.
from app.utils import pause, print_title


def print_menu() -> None:
    """사용자가 선택할 수 있는 실습 메뉴를 출력합니다."""
    # 프로그램 전체 제목을 출력합니다.
    print_title("LangGraph 핵심 개념 콘솔 학습 앱")
    # 실행 가능한 메뉴를 번호와 함께 출력합니다.
    print("1. State, Node, Edge 기본 선형 그래프")
    print("2. add_conditional_edges 조건부 분기")
    print("3. 반복 그래프와 종료 조건")
    print("4. Reducer를 이용한 상태 누적")
    print("5. MessagesState 메시지 누적")
    print("6. InMemorySaver와 thread_id 체크포인트")
    print("7. 노드 예외 처리와 fallback")
    print("8. Mermaid 그래프 구조 출력")
    print("0. 프로그램 종료")


def run_mermaid_demo() -> None:
    """기본 그래프와 조건부 그래프의 Mermaid 정의를 출력합니다."""
    # 기본 선형 그래프를 생성합니다.
    basic = basic_graph.build_basic_graph()
    # 기본 그래프의 Mermaid 문자열을 생성합니다.
    basic_mermaid = basic.get_graph().draw_mermaid()
    # 기본 그래프 Mermaid 구조를 출력합니다.
    print("[기본 선형 그래프 Mermaid]")
    print(basic_mermaid)
    # 조건부 분기 그래프를 생성합니다.
    conditional = conditional_graph.build_conditional_graph()
    # 조건부 그래프의 Mermaid 문자열을 생성합니다.
    conditional_mermaid = conditional.get_graph().draw_mermaid()
    # 조건부 그래프 Mermaid 구조를 출력합니다.
    print("\n[조건부 분기 그래프 Mermaid]")
    print(conditional_mermaid)


def main() -> None:
    """사용자가 종료할 때까지 메뉴를 반복 실행합니다."""
    # 프로그램을 계속 실행하기 위한 무한 반복문입니다.
    while True:
        # 매 반복마다 메뉴를 출력합니다.
        print_menu()
        # 사용자가 입력한 메뉴 번호의 앞뒤 공백을 제거합니다.
        choice = input("\n실행할 메뉴 번호를 입력하세요: ").strip()
        # 0번을 선택하면 프로그램을 종료합니다.
        if choice == "0":
            print("\nLangGraph 콘솔 학습 앱을 종료합니다.")
            break
        # 개별 실습 오류가 전체 프로그램 종료로 이어지지 않도록 처리합니다.
        try:
            # 1번은 기본 선형 그래프를 실행합니다.
            if choice == "1":
                print_title("1. State, Node, Edge 기본 선형 그래프")
                basic_graph.run_demo()
            # 2번은 조건부 분기 그래프를 실행합니다.
            elif choice == "2":
                print_title("2. add_conditional_edges 조건부 분기")
                conditional_graph.run_demo()
            # 3번은 반복과 종료 조건 예제를 실행합니다.
            elif choice == "3":
                print_title("3. 반복 그래프와 종료 조건")
                loop_graph.run_demo()
            # 4번은 Reducer 누적 예제를 실행합니다.
            elif choice == "4":
                print_title("4. Reducer를 이용한 상태 누적")
                reducer_graph.run_demo()
            # 5번은 MessagesState 예제를 실행합니다.
            elif choice == "5":
                print_title("5. MessagesState 메시지 누적")
                messages_graph.run_demo()
            # 6번은 Checkpointer 예제를 실행합니다.
            elif choice == "6":
                print_title("6. InMemorySaver와 thread_id 체크포인트")
                checkpoint_graph.run_demo()
            # 7번은 오류 처리 예제를 실행합니다.
            elif choice == "7":
                print_title("7. 노드 예외 처리와 fallback")
                error_graph.run_demo()
            # 8번은 Mermaid 그래프 정의를 출력합니다.
            elif choice == "8":
                print_title("8. Mermaid 그래프 구조 출력")
                run_mermaid_demo()
            # 정의되지 않은 번호이면 입력 오류를 안내합니다.
            else:
                print("\n[입력 오류] 0부터 8 사이의 메뉴 번호를 입력하세요.")
        except Exception as error:
            # 실습 중 발생한 예외 타입과 내용을 출력합니다.
            print(f"\n[실행 오류] {type(error).__name__}: {error}")
        # 결과를 읽을 수 있도록 Enter 입력을 기다립니다.
        pause()


# 이 파일을 직접 실행한 경우에만 main 함수를 호출합니다.
if __name__ == "__main__":
    # 콘솔 메뉴 애플리케이션을 시작합니다.
    main()
