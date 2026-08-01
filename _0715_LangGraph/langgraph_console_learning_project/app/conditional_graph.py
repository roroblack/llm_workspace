# -*- coding: utf-8 -*-
"""add_conditional_edges를 이용한 조건부 분기 예제입니다."""

# TypedDict는 상태 딕셔너리 구조를 선언할 때 사용합니다.
from typing import TypedDict

# LangGraph의 그래프 생성 요소를 가져옵니다.
from langgraph.graph import END, START, StateGraph


class RouterState(TypedDict):
    """질문 분류 그래프가 공유하는 상태입니다."""

    # 사용자가 입력한 질문을 저장합니다.
    question: str
    # policy 또는 sales 분류 결과를 저장합니다.
    category: str
    # 선택된 처리 노드의 답변을 저장합니다.
    answer: str


def classify_node(state: RouterState) -> dict:
    """질문을 정책 또는 상품 추천으로 분류합니다."""
    # 현재 상태에서 질문을 가져옵니다.
    question = state["question"]
    # 정책 질문을 판단할 키워드를 정의합니다.
    policy_words = ["환불", "교환", "배송", "취소", "적립", "포인트"]
    # 정책 키워드가 하나라도 포함되었는지 검사합니다.
    is_policy = any(word in question for word in policy_words)
    # 정책이면 policy, 아니면 sales를 선택합니다.
    category = "policy" if is_policy else "sales"
    # 분류 결과만 상태에 반영하도록 반환합니다.
    return {"category": category}


def route_question(state: RouterState) -> str:
    """category 값에 따라 다음 노드 이름을 반환합니다."""
    # 앞 노드가 저장한 category를 분기 키로 사용합니다.
    return state["category"]


def policy_node(state: RouterState) -> dict:
    """정책 질문을 처리하는 전문 노드입니다."""
    # 실제 프로젝트에서는 FAQ 또는 Vector DB 검색을 이 위치에 넣을 수 있습니다.
    answer = f"정책 담당 노드가 처리했습니다: {state['question']}"
    # 생성한 답변을 상태에 저장합니다.
    return {"answer": answer}


def sales_node(state: RouterState) -> dict:
    """상품 추천 질문을 처리하는 전문 노드입니다."""
    # 실제 프로젝트에서는 상품 DB 검색이나 추천 모델을 이 위치에 넣을 수 있습니다.
    answer = f"상품 추천 담당 노드가 처리했습니다: {state['question']}"
    # 생성한 답변을 상태에 저장합니다.
    return {"answer": answer}


def build_conditional_graph():
    """질문 분류 결과에 따라 서로 다른 노드로 이동하는 그래프를 생성합니다."""
    # RouterState를 공유 상태로 사용하는 그래프 빌더를 생성합니다.
    builder = StateGraph(RouterState)
    # 질문 분류 노드를 등록합니다.
    builder.add_node("classify", classify_node)
    # 정책 처리 노드를 등록합니다.
    builder.add_node("policy", policy_node)
    # 상품 추천 처리 노드를 등록합니다.
    builder.add_node("sales", sales_node)
    # START에서 classify 노드로 연결합니다.
    builder.add_edge(START, "classify")
    # classify 결과에 따라 policy 또는 sales로 분기합니다.
    builder.add_conditional_edges(
        "classify",
        route_question,
        {"policy": "policy", "sales": "sales"},
    )
    # policy 노드 실행 후 종료합니다.
    builder.add_edge("policy", END)
    # sales 노드 실행 후 종료합니다.
    builder.add_edge("sales", END)
    # 그래프를 실행 가능한 객체로 컴파일합니다.
    return builder.compile()


def run_demo() -> None:
    """정책 질문과 추천 질문을 각각 실행해 분기 결과를 확인합니다."""
    # 조건부 분기 그래프를 생성합니다.
    graph = build_conditional_graph()
    # 서로 다른 경로를 확인하기 위한 질문 목록을 준비합니다.
    questions = [
        "환불은 며칠 이내에 가능한가요?",
        "가성비 좋은 전자기기를 추천해 주세요.",
    ]
    # 질문을 하나씩 그래프에 전달합니다.
    for question in questions:
        # 질문마다 새로운 초기 상태를 만듭니다.
        result = graph.invoke({"question": question, "category": "", "answer": ""})
        # 원본 질문을 출력합니다.
        print("\n질문:", question)
        # 분류 결과를 출력합니다.
        print("분류:", result["category"])
        # 최종 답변을 출력합니다.
        print("답변:", result["answer"])
