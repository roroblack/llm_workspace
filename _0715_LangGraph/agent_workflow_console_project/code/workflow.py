# -*- coding: utf-8 -*-
"""LangGraph 기반 CS 티켓 처리 워크플로우의 핵심 기능을 정의합니다."""

# 타입이 정해진 딕셔너리 상태를 만들기 위해 TypedDict와 NotRequired를 가져옵니다.
from typing import NotRequired, TypedDict

# LangChain 채팅 모델에 전달할 시스템 메시지와 사용자 메시지를 가져옵니다.
from langchain_core.messages import HumanMessage, SystemMessage

# 상태 기반 그래프와 시작/종료 가상 노드를 가져옵니다.
from langgraph.graph import END, START, StateGraph

# 공통 모듈의 채팅 모델 생성 함수를 가져옵니다.
from common import get_chat


# API와 그래프에 의존하지 않는 순수 파이썬 규칙 함수를 가져옵니다.
from rules import (
    CATEGORIES,
    calculate_priority,
    calculate_route,
    calculate_team,
    normalize_category,
)


class TicketState(TypedDict):
    """모든 노드가 공유하며 단계별 결과를 누적하는 상태 스키마입니다."""

    # 사용자가 입력한 CS 티켓 원문입니다.
    content: str

    # 분류 노드가 채우는 카테고리 값입니다.
    category: NotRequired[str]

    # 우선순위 노드가 채우는 긴급도 값입니다.
    priority: NotRequired[str]

    # 마지막 배정 노드가 채우는 담당팀입니다.
    team: NotRequired[str]

    # 긴급 티켓의 알림 노드가 채우는 즉시 알림 표시입니다.
    alert: NotRequired[str]

    # 검증 실패 또는 API 예외 내용을 기록합니다.
    error: NotRequired[str]


def append_error(state: TicketState, message: str) -> str:
    """기존 오류를 지우지 않고 새 노드 오류 메시지를 뒤에 누적합니다."""

    # 이전 노드가 남긴 오류가 있을 수 있으므로 문자열로 안전하게 읽습니다.
    previous_error = str(state.get("error") or "").strip()

    # 기존 오류와 새 오류가 모두 있으면 구분자를 넣어 추적 가능하게 합칩니다.
    return f"{previous_error} | {message}" if previous_error else message


def node_error(state: TicketState, node_name: str, exc: Exception) -> str:
    """예외를 어느 노드에서 발생했는지 알 수 있는 상태 메시지로 변환합니다."""

    # 예외 클래스와 설명을 함께 기록하여 원인 확인을 쉽게 합니다.
    message = f"{node_name} 노드 예외: {type(exc).__name__}: {exc}"

    # 앞 단계의 오류가 있다면 덮어쓰지 않고 함께 보존합니다.
    return append_error(state, message)


def message_to_text(response: object) -> str:
    """LangChain 공급자별 응답 형식을 안전하게 일반 문자열로 변환합니다."""

    # 대부분의 LangChain AIMessage는 content 속성에 최종 응답을 저장합니다.
    content = getattr(response, "content", response)

    # 일반 문자열이면 앞뒤 공백을 제거해 바로 반환합니다.
    if isinstance(content, str):
        return content.strip()

    # 일부 모델은 여러 콘텐츠 블록을 리스트로 반환할 수 있습니다.
    if isinstance(content, list):
        # 최종 문자열 조각을 순서대로 모을 임시 리스트입니다.
        text_parts: list[str] = []

        # 리스트에 포함된 각 콘텐츠 블록을 차례로 확인합니다.
        for item in content:
            # 블록이 딕셔너리이고 text 키가 있으면 실제 텍스트만 추가합니다.
            if isinstance(item, dict) and "text" in item:
                text_parts.append(str(item["text"]))
            # 다른 형식은 정보 유실을 막기 위해 문자열로 변환하여 추가합니다.
            else:
                text_parts.append(str(item))

        # 여러 조각을 하나의 문장으로 합치고 앞뒤 공백을 제거합니다.
        return " ".join(text_parts).strip()

    # 예상하지 못한 형식도 프로그램이 중단되지 않도록 문자열로 변환합니다.
    return str(content).strip()



def make_classify_node(provider: str, llm: object | None = None):
    """선택한 LLM 공급자를 사용하는 분류 노드 함수를 생성합니다."""

    # 테스트용 모델이 없으면 실제 공급자 모델을 temperature 0으로 생성합니다.
    if llm is None:
        llm = get_chat(provider=provider, temperature=0.0)

    def classify_node(state: TicketState) -> dict:
        """티켓 내용을 LLM으로 분류하고 출력값을 허용 목록으로 검증합니다."""

        try:
            # 티켓 내용이 없을 수도 있으므로 get과 기본값으로 안전하게 읽습니다.
            content = state.get("content", "").strip()

            # 빈 입력은 불필요한 API 호출 없이 기타로 보정하고 오류를 기록합니다.
            if not content:
                return {
                    "category": "기타",
                    "error": append_error(state, "빈 티켓 내용 → 기타 보정"),
                }

            # 모델의 역할과 출력 형식을 강제하는 시스템 메시지를 작성합니다.
            system_message = SystemMessage(
                content=(
                    f"다음 CS 티켓을 {CATEGORIES} 중 정확히 하나로 분류하세요. "
                    "설명 없이 카테고리 단어만 출력하세요."
                )
            )

            # 실제 사용자가 입력한 티켓 내용을 HumanMessage로 작성합니다.
            human_message = HumanMessage(content=content)

            # 시스템 메시지와 사용자 메시지를 모델에 전달하여 분류 결과를 받습니다.
            response = llm.invoke([system_message, human_message])

            # 공급자별 응답 구조 차이를 흡수하여 일반 문자열로 변환합니다.
            raw_output = message_to_text(response)

            # 허용 목록 검증과 부분 매칭 보정을 수행합니다.
            category, error = normalize_category(raw_output)

            # 정상 분류에서는 기존 오류를 건드리지 않고 카테고리만 업데이트합니다.
            if not error:
                return {"category": category}

            # 보정 오류는 이전 노드 오류와 함께 상태에 누적합니다.
            return {"category": category, "error": append_error(state, error)}
        except Exception as exc:
            # 분류 실패가 전체 배치를 중단시키지 않도록 기타로 폴백합니다.
            return {"category": "기타", "error": node_error(state, "classify", exc)}

    # 공급자가 연결된 실제 분류 노드 함수를 호출자에게 반환합니다.
    return classify_node


def priority_node(state: TicketState) -> dict:
    """카테고리와 키워드를 이용해 LLM 없이 우선순위를 계산합니다."""

    try:
        # 입력 티켓 내용을 안전하게 문자열로 읽습니다.
        text = state.get("content", "")

        # 이전 분류 노드가 채운 카테고리를 읽되 없으면 기타로 처리합니다.
        category = state.get("category", "기타")

        # 외부 의존성이 없는 공통 규칙 함수로 우선순위를 계산합니다.
        priority = calculate_priority(text, category)

        # 새로 계산한 priority 필드만 상태 업데이트 값으로 반환합니다.
        return {"priority": priority}
    except Exception as exc:
        # 다음 조건 분기와 배정이 계속 실행되도록 안전한 기본 우선순위를 제공합니다.
        return {"priority": "보통", "error": node_error(state, "priority", exc)}


def assign_node(state: TicketState) -> dict:
    """카테고리별 담당팀 매핑 규칙으로 팀을 배정합니다."""

    try:
        # 앞선 어느 노드든 오류를 남겼다면 최종 담당팀을 검토필요로 덮어씁니다.
        if state.get("error"):
            return {"team": "검토필요"}

        # 분류 결과가 없거나 매핑에 없을 때를 대비해 기본값 기타를 사용합니다.
        category = state.get("category", "기타")

        # 외부 의존성이 없는 공통 규칙 함수로 담당팀을 계산합니다.
        team = calculate_team(category)

        # 배정 결과인 team 필드만 반환합니다.
        return {"team": team}
    except Exception as exc:
        # 마지막 배정 노드 자체가 실패해도 오류와 검토필요 팀을 최종 상태에 남깁니다.
        return {"team": "검토필요", "error": node_error(state, "assign", exc)}


def route_by_priority(state: TicketState) -> str:
    """우선순위를 읽어 긴급 경로 또는 일반 배정 경로 이름을 반환합니다."""

    # 외부 의존성이 없는 공통 라우팅 함수로 다음 노드 이름을 결정합니다.
    return calculate_route(state.get("priority", "보통"))


def notify_node(state: TicketState) -> dict:
    """긴급 티켓에만 즉시 알림 표시를 추가합니다."""

    try:
        # 이 노드는 긴급 조건에서만 호출되지만 직접 호출하는 경우까지 안전하게 검사합니다.
        if state.get("priority") == "긴급":
            return {"alert": "즉시알림"}

        # 긴급이 아니면 알림 값을 만들지 않습니다.
        return {}
    except Exception as exc:
        # 알림 실패도 마지막 배정 노드가 검토필요로 처리할 수 있도록 기록합니다.
        return {"error": node_error(state, "notify", exc)}


def build_linear_workflow(provider: str, llm: object | None = None):
    """분류 → 우선순위 → 배정 순서가 고정된 선형 워크플로우를 만듭니다."""

    # TicketState 스키마를 공유 상태로 사용하는 그래프 빌더를 생성합니다.
    graph_builder = StateGraph(TicketState)

    # 선택한 공급자를 사용하는 분류 노드를 classify라는 이름으로 등록합니다.
    graph_builder.add_node("classify", make_classify_node(provider, llm=llm))

    # 규칙 기반 우선순위 노드를 priority라는 이름으로 등록합니다.
    graph_builder.add_node("priority", priority_node)

    # 규칙 기반 팀 배정 노드를 assign이라는 이름으로 등록합니다.
    graph_builder.add_node("assign", assign_node)

    # 시작 지점 다음에 반드시 분류 노드가 실행되도록 연결합니다.
    graph_builder.add_edge(START, "classify")

    # 분류 다음에 반드시 우선순위 노드가 실행되도록 연결합니다.
    graph_builder.add_edge("classify", "priority")

    # 우선순위 다음에 반드시 배정 노드가 실행되도록 연결합니다.
    graph_builder.add_edge("priority", "assign")

    # 배정이 끝나면 워크플로우를 종료하도록 연결합니다.
    graph_builder.add_edge("assign", END)

    # 선언한 노드와 엣지를 실제 실행 가능한 그래프로 컴파일하여 반환합니다.
    return graph_builder.compile()


def build_conditional_workflow(provider: str, llm: object | None = None):
    """긴급 티켓과 일반 티켓이 서로 다른 경로를 타는 조건부 워크플로우를 만듭니다."""

    # TicketState를 공유 상태로 사용하는 새 그래프 빌더를 생성합니다.
    graph_builder = StateGraph(TicketState)

    # LLM 기반 분류 노드를 등록합니다.
    graph_builder.add_node("classify", make_classify_node(provider, llm=llm))

    # 규칙 기반 우선순위 노드를 등록합니다.
    graph_builder.add_node("priority", priority_node)

    # 긴급 티켓에 즉시 알림을 표시할 노드를 등록합니다.
    graph_builder.add_node("notify", notify_node)

    # 긴급/일반 티켓이 최종적으로 거치는 담당팀 배정 노드를 등록합니다.
    graph_builder.add_node("assign", assign_node)

    # 시작에서 분류까지의 고정 엣지를 연결합니다.
    graph_builder.add_edge(START, "classify")

    # 분류에서 우선순위까지의 고정 엣지를 연결합니다.
    graph_builder.add_edge("classify", "priority")

    # priority 다음 노드는 route_by_priority의 반환값에 따라 동적으로 선택합니다.
    graph_builder.add_conditional_edges(
        "priority",
        route_by_priority,
        {"notify": "notify", "assign": "assign"},
    )

    # 긴급 알림 이후에도 담당팀 배정 노드를 반드시 실행합니다.
    graph_builder.add_edge("notify", "assign")

    # 일반 경로 처리가 끝나면 그래프를 종료합니다.
    graph_builder.add_edge("assign", END)

    # 조건부 분기가 포함된 실행 가능한 그래프를 반환합니다.
    return graph_builder.compile()
