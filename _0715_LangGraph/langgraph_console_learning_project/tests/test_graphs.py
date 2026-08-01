# -*- coding: utf-8 -*-
"""외부 API 키 없이 실행할 수 있는 LangGraph 단위 테스트입니다."""

# 테스트할 그래프 생성 함수를 가져옵니다.
from app.basic_graph import build_basic_graph
from app.conditional_graph import build_conditional_graph
from app.loop_graph import build_loop_graph
from app.reducer_graph import build_reducer_graph


def test_basic_graph() -> None:
    """기본 그래프가 문자 수를 올바르게 계산하는지 확인합니다."""
    # 기본 그래프를 생성합니다.
    graph = build_basic_graph()
    # 간단한 문자열을 초기 상태로 전달합니다.
    result = graph.invoke({"text": "abc", "length": 0, "result": ""})
    # 문자열 길이가 3인지 확인합니다.
    assert result["length"] == 3
    # 최종 문장에 문자 수가 포함됐는지 확인합니다.
    assert "문자 수: 3" in result["result"]


def test_conditional_graph_policy_route() -> None:
    """환불 질문이 policy 경로로 분류되는지 확인합니다."""
    # 조건부 그래프를 생성합니다.
    graph = build_conditional_graph()
    # 환불 질문을 그래프에 전달합니다.
    result = graph.invoke({"question": "환불 기간", "category": "", "answer": ""})
    # 분류 결과가 policy인지 확인합니다.
    assert result["category"] == "policy"
    # 정책 처리 노드가 실행됐는지 확인합니다.
    assert "정책 담당" in result["answer"]


def test_loop_graph_stops_at_three() -> None:
    """반복 그래프가 count 3에서 종료되는지 확인합니다."""
    # 반복 그래프를 생성합니다.
    graph = build_loop_graph()
    # count 0부터 실행합니다.
    result = graph.invoke({"count": 0, "message": ""})
    # 최종 count가 정확히 3인지 확인합니다.
    assert result["count"] == 3


def test_reducer_graph_accumulates_logs() -> None:
    """Reducer가 세 로그를 모두 누적하는지 확인합니다."""
    # Reducer 그래프를 생성합니다.
    graph = build_reducer_graph()
    # 빈 로그 리스트로 실행합니다.
    result = graph.invoke({"logs": []})
    # 누적된 로그 개수가 3인지 확인합니다.
    assert len(result["logs"]) == 3
