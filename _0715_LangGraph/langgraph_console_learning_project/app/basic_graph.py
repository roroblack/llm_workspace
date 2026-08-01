# -*- coding: utf-8 -*-
"""State, Node, Edge의 기본 구조를 확인하는 선형 그래프 예제입니다."""

# TypedDict는 상태 딕셔너리의 키와 타입을 선언할 때 사용합니다.
from typing import TypedDict

# StateGraph는 상태 기반 그래프를 생성합니다.
# START와 END는 그래프의 시작점과 종료점을 나타냅니다.
from langgraph.graph import END, START, StateGraph


class BasicState(TypedDict):
    """그래프의 모든 노드가 공유하는 상태 구조입니다."""

    # 사용자가 입력한 원본 문장을 저장합니다.
    text: str
    # 입력 문장의 문자 수를 저장합니다.
    length: int
    # 최종 출력 문장을 저장합니다.
    result: str


def measure_node(state: BasicState) -> dict:
    """입력 문장의 문자 수를 계산합니다."""
    # 공유 상태에서 원본 문장을 읽습니다.
    text = state["text"]
    # len 함수를 사용해 문자열 길이를 계산합니다.
    length = len(text)
    # 변경한 length 값만 반환하면 LangGraph가 기존 상태에 병합합니다.
    return {"length": length}


def format_node(state: BasicState) -> dict:
    """원본 문장과 길이를 최종 결과 문자열로 구성합니다."""
    # 기존 상태에 유지된 원본 문장을 읽습니다.
    text = state["text"]
    # 앞 노드가 계산한 길이를 읽습니다.
    length = state["length"]
    # 사용자에게 보여 줄 최종 문자열을 만듭니다.
    result = f"입력 문장: {text} / 문자 수: {length}"
    # 새로 만든 result 값만 반환합니다.
    return {"result": result}


def build_basic_graph():
    """START → measure → format → END 그래프를 생성합니다."""
    # BasicState를 공유 상태로 사용하는 그래프 빌더를 만듭니다.
    builder = StateGraph(BasicState)
    # measure라는 이름으로 문자 수 계산 노드를 등록합니다.
    builder.add_node("measure", measure_node)
    # format이라는 이름으로 결과 구성 노드를 등록합니다.
    builder.add_node("format", format_node)
    # 그래프 시작 후 measure 노드가 실행되도록 연결합니다.
    builder.add_edge(START, "measure")
    # measure 다음에 format 노드가 실행되도록 연결합니다.
    builder.add_edge("measure", "format")
    # format 실행 후 그래프가 종료되도록 연결합니다.
    builder.add_edge("format", END)
    # 정의한 그래프를 실행 가능한 객체로 컴파일합니다.
    return builder.compile()


def run_demo() -> None:
    """기본 그래프를 실행하고 최종 상태를 출력합니다."""
    # 실행 가능한 기본 그래프를 생성합니다.
    graph = build_basic_graph()
    # 그래프 실행에 사용할 초기 상태를 준비합니다.
    initial_state: BasicState = {
        "text": "LangGraph를 학습합니다.",
        "length": 0,
        "result": "",
    }
    # invoke로 그래프를 동기 실행합니다.
    final_state = graph.invoke(initial_state)
    # 모든 노드 실행이 끝난 최종 상태를 출력합니다.
    print("최종 상태:", final_state)
    # 최종 결과 문자열만 별도로 출력합니다.
    print("최종 결과:", final_state["result"])
