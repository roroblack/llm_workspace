# -*- coding: utf-8 -*-
"""조건부 엣지를 이용한 반복과 종료 조건 예제입니다."""

# TypedDict는 반복 그래프 상태 구조를 선언합니다.
from typing import TypedDict

# LangGraph 그래프 구성 요소를 가져옵니다.
from langgraph.graph import END, START, StateGraph


class LoopState(TypedDict):
    """반복 횟수와 메시지를 저장하는 상태입니다."""

    # 현재 반복 횟수를 저장합니다.
    count: int
    # 현재 반복 처리 상태를 저장합니다.
    message: str


def increase_node(state: LoopState) -> dict:
    """count 값을 1 증가시킵니다."""
    # 기존 count 값에 1을 더합니다.
    next_count = state["count"] + 1
    # 증가한 횟수를 설명하는 문자열을 만듭니다.
    message = f"{next_count}번째 반복 실행이 완료되었습니다."
    # 변경된 값을 상태 업데이트 결과로 반환합니다.
    return {"count": next_count, "message": message}


def should_continue(state: LoopState) -> str:
    """count가 3 미만이면 반복하고, 아니면 종료합니다."""
    # count가 3보다 작으면 repeat 경로를 선택합니다.
    if state["count"] < 3:
        return "repeat"
    # count가 3 이상이면 finish 경로를 선택합니다.
    return "finish"


def build_loop_graph():
    """최대 3회 반복하는 그래프를 생성합니다."""
    # LoopState를 사용하는 그래프 빌더를 생성합니다.
    builder = StateGraph(LoopState)
    # 반복 실행할 increase 노드를 등록합니다.
    builder.add_node("increase", increase_node)
    # START에서 increase로 연결합니다.
    builder.add_edge(START, "increase")
    # increase 실행 후 반복 또는 종료 경로를 선택합니다.
    builder.add_conditional_edges(
        "increase",
        should_continue,
        {"repeat": "increase", "finish": END},
    )
    # 실행 가능한 그래프로 컴파일합니다.
    return builder.compile()


def run_demo() -> None:
    """stream과 invoke로 반복 그래프를 확인합니다."""
    # 반복 그래프를 생성합니다.
    graph = build_loop_graph()
    # count를 0으로 설정한 초기 상태를 준비합니다.
    initial_state: LoopState = {"count": 0, "message": ""}
    # stream을 사용해 각 노드의 중간 이벤트를 출력합니다.
    for event in graph.stream(initial_state):
        # 실행된 노드와 해당 노드의 반환값을 확인합니다.
        print("중간 이벤트:", event)
    # invoke를 사용해 최종 상태를 별도로 확인합니다.
    final_state = graph.invoke(initial_state)
    # 반복이 count 3에서 종료됐는지 출력합니다.
    print("최종 상태:", final_state)
