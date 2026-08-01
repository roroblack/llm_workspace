# -*- coding: utf-8 -*-
"""Reducer를 사용해 리스트 값을 누적하는 예제입니다."""

# operator.add는 기존 리스트와 새 리스트를 더하는 Reducer로 사용합니다.
import operator

# Annotated는 상태 필드에 Reducer 정보를 지정합니다.
# TypedDict는 상태 구조를 선언합니다.
from typing import Annotated, TypedDict

# LangGraph 그래프 구성 요소를 가져옵니다.
from langgraph.graph import END, START, StateGraph


class ReducerState(TypedDict):
    """실행 로그를 리스트에 누적하는 상태입니다."""

    # 각 노드가 반환한 리스트를 기존 리스트 뒤에 이어 붙입니다.
    logs: Annotated[list[str], operator.add]


def first_node(state: ReducerState) -> dict:
    """첫 번째 로그를 추가합니다."""
    # 기존 목록을 직접 수정하지 않고 새 항목만 반환합니다.
    return {"logs": ["첫 번째 노드 실행"]}


def second_node(state: ReducerState) -> dict:
    """두 번째 로그를 추가합니다."""
    # Reducer가 이 리스트를 기존 logs 뒤에 자동으로 결합합니다.
    return {"logs": ["두 번째 노드 실행"]}


def third_node(state: ReducerState) -> dict:
    """세 번째 로그를 추가합니다."""
    # 세 번째 실행 기록을 반환합니다.
    return {"logs": ["세 번째 노드 실행"]}


def build_reducer_graph():
    """세 노드의 로그가 누적되는 그래프를 생성합니다."""
    # ReducerState를 사용하는 그래프 빌더를 생성합니다.
    builder = StateGraph(ReducerState)
    # 로그를 추가하는 노드를 등록합니다.
    builder.add_node("first", first_node)
    builder.add_node("second", second_node)
    builder.add_node("third", third_node)
    # 세 노드가 순차적으로 실행되도록 연결합니다.
    builder.add_edge(START, "first")
    builder.add_edge("first", "second")
    builder.add_edge("second", "third")
    builder.add_edge("third", END)
    # 실행 가능한 그래프로 컴파일합니다.
    return builder.compile()


def run_demo() -> None:
    """Reducer가 로그를 누적하는 결과를 출력합니다."""
    # Reducer 그래프를 생성합니다.
    graph = build_reducer_graph()
    # 빈 로그 리스트로 그래프를 실행합니다.
    result = graph.invoke({"logs": []})
    # 누적된 로그의 제목을 출력합니다.
    print("누적 로그:")
    # 각 로그에 번호를 붙여 출력합니다.
    for index, log in enumerate(result["logs"], start=1):
        print(f"{index}. {log}")
