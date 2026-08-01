# -*- coding: utf-8 -*-
"""노드 예외 처리와 fallback 분기 예제입니다."""

# TypedDict는 오류 처리 상태 구조를 선언합니다.
from typing import TypedDict

# LangGraph 그래프 구성 요소를 가져옵니다.
from langgraph.graph import END, START, StateGraph


class ErrorState(TypedDict):
    """입력값, 처리 결과, 오류 메시지를 공유하는 상태입니다."""

    # 처리할 원본 입력값을 저장합니다.
    value: str
    # 정상 처리 또는 fallback 결과를 저장합니다.
    result: str
    # 발생한 오류 메시지를 저장합니다.
    error: str


def risky_node(state: ErrorState) -> dict:
    """빈 문자열 입력 시 오류 상태를 반환합니다."""
    try:
        # 상태에서 입력 문자열을 읽습니다.
        value = state["value"]
        # 공백을 제거한 값이 비어 있으면 예외를 발생시킵니다.
        if not value.strip():
            raise ValueError("빈 문자열은 처리할 수 없습니다.")
        # 정상 입력은 대문자로 변환합니다.
        result = value.upper()
        # 정상 결과와 빈 오류 메시지를 반환합니다.
        return {"result": result, "error": ""}
    except Exception as error:
        # 예외를 다시 던지지 않고 상태의 error 필드에 기록합니다.
        return {"result": "", "error": f"risky_node 오류: {error}"}


def route_after_risky(state: ErrorState) -> str:
    """오류 발생 여부에 따라 success 또는 fallback 경로를 선택합니다."""
    # error 값이 존재하면 fallback 경로를 선택합니다.
    if state["error"]:
        return "fallback"
    # 오류가 없으면 success 경로를 선택합니다.
    return "success"


def success_node(state: ErrorState) -> dict:
    """정상 처리 결과를 최종 문장으로 만듭니다."""
    # 앞 노드의 결과를 포함한 성공 메시지를 생성합니다.
    result = f"정상 처리 완료: {state['result']}"
    # 최종 결과를 상태에 저장합니다.
    return {"result": result}


def fallback_node(state: ErrorState) -> dict:
    """오류 발생 시 안전한 기본 결과를 생성합니다."""
    # 오류 내용을 포함하는 fallback 메시지를 만듭니다.
    result = f"안전한 기본 처리로 전환했습니다. 원인: {state['error']}"
    # fallback 결과를 상태에 저장합니다.
    return {"result": result}


def build_error_graph():
    """오류 상태에 따라 success 또는 fallback으로 분기하는 그래프를 생성합니다."""
    # ErrorState를 공유 상태로 사용하는 그래프 빌더를 생성합니다.
    builder = StateGraph(ErrorState)
    # 위험 처리, 정상 처리, fallback 처리 노드를 등록합니다.
    builder.add_node("risky", risky_node)
    builder.add_node("success", success_node)
    builder.add_node("fallback", fallback_node)
    # START에서 risky 노드로 연결합니다.
    builder.add_edge(START, "risky")
    # risky 결과에 따라 success 또는 fallback으로 분기합니다.
    builder.add_conditional_edges(
        "risky",
        route_after_risky,
        {"success": "success", "fallback": "fallback"},
    )
    # 두 경로 모두 처리 후 그래프를 종료합니다.
    builder.add_edge("success", END)
    builder.add_edge("fallback", END)
    # 실행 가능한 그래프로 컴파일합니다.
    return builder.compile()


def run_demo() -> None:
    """정상 입력과 빈 입력을 각각 실행합니다."""
    # 오류 처리 그래프를 생성합니다.
    graph = build_error_graph()
    # 정상 입력과 오류 입력을 준비합니다.
    values = ["langgraph", ""]
    # 각 값을 그래프에 전달합니다.
    for value in values:
        # 입력마다 새로운 초기 상태를 만듭니다.
        result = graph.invoke({"value": value, "result": "", "error": ""})
        # 실제 입력값을 repr 형태로 출력합니다.
        print(f"\n입력값: {value!r}")
        # 최종 결과를 출력합니다.
        print("결과:", result["result"])
        # 오류가 없으면 '없음'을 출력합니다.
        print("오류:", result["error"] or "없음")
