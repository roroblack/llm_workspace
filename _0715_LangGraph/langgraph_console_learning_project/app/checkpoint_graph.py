# -*- coding: utf-8 -*-
"""InMemorySaver와 thread_id를 이용한 체크포인트 예제입니다."""

# AIMessage와 HumanMessage는 대화 메시지 객체를 생성합니다.
from langchain_core.messages import AIMessage, HumanMessage

# InMemorySaver는 프로그램 실행 중 상태를 메모리에 저장합니다.
from langgraph.checkpoint.memory import InMemorySaver

# MessagesState와 그래프 구성 요소를 가져옵니다.
from langgraph.graph import END, START, MessagesState, StateGraph


def memory_node(state: MessagesState) -> dict:
    """현재 thread에 저장된 전체 메시지 수를 응답합니다."""
    # Checkpointer가 복원한 과거 메시지를 포함해 전체 개수를 계산합니다.
    message_count = len(state["messages"])
    # 현재 메시지 개수를 설명하는 AI 응답을 생성합니다.
    answer = AIMessage(content=f"현재 thread에 저장된 전체 메시지는 {message_count}개입니다.")
    # 생성한 AI 응답을 messages에 누적하도록 반환합니다.
    return {"messages": [answer]}


def build_checkpoint_graph():
    """메모리 Checkpointer가 적용된 메시지 그래프를 생성합니다."""
    # 상태를 메모리에 저장할 Checkpointer를 만듭니다.
    memory = InMemorySaver()
    # MessagesState 기반 그래프 빌더를 생성합니다.
    builder = StateGraph(MessagesState)
    # 메모리 확인 노드를 등록합니다.
    builder.add_node("memory", memory_node)
    # START에서 memory 노드로 연결합니다.
    builder.add_edge(START, "memory")
    # memory 실행 후 그래프를 종료합니다.
    builder.add_edge("memory", END)
    # compile 시 checkpointer를 전달해 상태 저장 기능을 활성화합니다.
    graph = builder.compile(checkpointer=memory)
    # 그래프와 Checkpointer를 함께 반환합니다.
    return graph, memory


def run_demo() -> None:
    """같은 thread_id로 두 번 실행해 과거 상태 복원을 확인합니다."""
    # 체크포인트 그래프를 생성합니다.
    graph, _memory = build_checkpoint_graph()
    # 동일한 대화 세션을 구분할 thread_id를 설정합니다.
    config = {"configurable": {"thread_id": "langgraph-learning-thread"}}
    # 첫 번째 사용자 메시지를 실행합니다.
    first_result = graph.invoke(
        {"messages": [HumanMessage(content="첫 번째 질문입니다.")]},
        config=config,
    )
    # 첫 번째 실행의 마지막 AI 응답을 출력합니다.
    print("첫 번째 실행:", first_result["messages"][-1].content)
    # 같은 thread_id로 두 번째 사용자 메시지를 실행합니다.
    second_result = graph.invoke(
        {"messages": [HumanMessage(content="이전 상태를 기억하나요?")]},
        config=config,
    )
    # 두 번째 실행에서는 이전 메시지가 복원되어 전체 개수가 증가합니다.
    print("두 번째 실행:", second_result["messages"][-1].content)
    # 최종 메시지 전체를 출력합니다.
    print("\n최종 메시지 목록:")
    # 최종 상태의 메시지를 순서대로 출력합니다.
    for index, message in enumerate(second_result["messages"], start=1):
        print(f"{index}. {type(message).__name__}: {message.content}")
