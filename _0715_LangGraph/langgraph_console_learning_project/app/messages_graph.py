# -*- coding: utf-8 -*-
"""MessagesState를 이용한 메시지 누적 예제입니다."""

# AIMessage와 HumanMessage는 대화 메시지 객체를 생성할 때 사용합니다.
from langchain_core.messages import AIMessage, HumanMessage

# MessagesState는 messages 필드와 메시지 누적 Reducer가 포함된 기본 상태입니다.
from langgraph.graph import END, START, MessagesState, StateGraph


def echo_node(state: MessagesState) -> dict:
    """가장 최근 사용자 메시지를 읽고 AI 응답을 생성합니다."""
    # 현재 메시지 목록의 마지막 메시지를 가져옵니다.
    last_message = state["messages"][-1]
    # 마지막 메시지 내용을 포함한 응답 문자열을 만듭니다.
    answer_text = f"LangGraph 노드가 입력을 확인했습니다: {last_message.content}"
    # AIMessage 객체를 반환하면 기존 messages 목록에 자동으로 누적됩니다.
    return {"messages": [AIMessage(content=answer_text)]}


def build_messages_graph():
    """사용자 메시지에 응답하는 메시지 그래프를 생성합니다."""
    # MessagesState를 공유 상태로 사용하는 그래프 빌더를 생성합니다.
    builder = StateGraph(MessagesState)
    # echo 노드를 등록합니다.
    builder.add_node("echo", echo_node)
    # START에서 echo 노드로 연결합니다.
    builder.add_edge(START, "echo")
    # echo 실행 후 그래프를 종료합니다.
    builder.add_edge("echo", END)
    # 실행 가능한 그래프로 컴파일합니다.
    return builder.compile()


def run_demo() -> None:
    """사용자 메시지와 AI 응답이 누적되는지 확인합니다."""
    # 메시지 그래프를 생성합니다.
    graph = build_messages_graph()
    # 사용자 메시지를 초기 상태로 전달해 그래프를 실행합니다.
    result = graph.invoke(
        {"messages": [HumanMessage(content="MessagesState의 역할을 확인합니다.")]}
    )
    # 최종 messages 목록을 순서대로 출력합니다.
    for index, message in enumerate(result["messages"], start=1):
        # 메시지 객체의 클래스 이름을 확인합니다.
        message_type = type(message).__name__
        # 메시지 번호, 타입, 내용을 출력합니다.
        print(f"{index}. {message_type}: {message.content}")
