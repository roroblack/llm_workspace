# -*- coding: utf-8 -*-
"""실습문제 1 해답: Writer 뒤에 Reviewer와 Finalize 노드를 추가합니다."""

# 기본 상태를 확장하고 기본 노드 팩토리와 데이터 로더를 재사용합니다.
from code_app.ai_team import TeamState as BaseTeamState
from code_app.ai_team import create_nodes, load_competitor_text
# 제공된 common.py로 선택한 모델 공급자의 LLM을 생성합니다.
from code_app.common_bridge import get_chat
# LLM 메시지의 역할과 입력을 구분합니다.
from langchain_core.messages import HumanMessage, SystemMessage
# 다섯 노드의 순서를 StateGraph로 선언합니다.
from langgraph.graph import END, START, StateGraph


class ReviewTeamState(BaseTeamState):
    """기본 상태에 검토 의견과 최종 수정본 칸을 추가합니다."""

    # review는 Reviewer가 작성한 사실성·가독성·구성 개선 의견입니다.
    review: str
    # final은 검토 의견을 반영해 Finalize 노드가 작성한 최종본입니다.
    final: str


def build_review_team(provider: str):
    """Researcher → Analyst → Writer → Reviewer → Finalize 그래프를 구성합니다."""

    # 기본 세 역할은 베이스 코드의 provider 선택형 노드를 그대로 사용합니다.
    researcher, analyst, writer = create_nodes(provider)
    # 검토와 최종 수정은 일관성을 높이기 위해 낮은 temperature로 별도 모델을 만듭니다.
    llm = get_chat(provider=provider, temperature=0.2)

    def reviewer(state: ReviewTeamState) -> dict[str, str]:
        """초안의 사실성·가독성·구성을 검토하고 개선점만 작성합니다."""

        # Reviewer가 보고서를 직접 다시 쓰지 않도록 역할 경계를 명확히 지정합니다.
        system = SystemMessage(
            "너는 보고서 검토자다. 리포트의 사실성, 가독성, 구성을 평가하고 "
            "개선할 점을 3가지 이내로 구체적으로 지적하라. 보고서를 다시 쓰지는 마라."
        )
        # Writer가 만든 report만 검토 대상으로 전달합니다.
        human = HumanMessage(f"[검토할 리포트]\n{state['report']}")
        # 검토 모델을 실행해 텍스트 의견을 가져옵니다.
        output = llm.invoke([system, human]).content
        # 사용자에게 Reviewer 노드 완료를 알립니다.
        print("  [reviewer] 검토 의견 작성 완료")
        # review 칸만 갱신하도록 반환합니다.
        return {"review": str(output)}

    def finalize(state: ReviewTeamState) -> dict[str, str]:
        """기존 리포트에 검토 의견을 반영해 최종 수정본을 작성합니다."""

        # Finalize가 원문과 검토 의견을 모두 사용하도록 시스템 역할을 설정합니다.
        system = SystemMessage(
            "너는 최종 보고서 편집자다. 기존 리포트의 사실을 유지하면서 검토 의견을 반영해 "
            "더 명확하고 실행 가능한 최종 마크다운 보고서를 작성하라."
        )
        # 초안과 검토 의견을 구분된 섹션으로 함께 전달합니다.
        human = HumanMessage(f"[기존 리포트]\n{state['report']}\n\n[검토 의견]\n{state['review']}")
        # 최종 수정 모델을 호출합니다.
        output = llm.invoke([system, human]).content
        # 사용자에게 Finalize 노드 완료를 알립니다.
        print("  [finalize] 최종본 작성 완료")
        # final 칸만 갱신하도록 반환합니다.
        return {"final": str(output)}

    # 확장된 ReviewTeamState를 사용하는 그래프를 생성합니다.
    graph = StateGraph(ReviewTeamState)
    # 기본 세 노드와 새로 추가한 두 노드를 등록합니다.
    graph.add_node("researcher", researcher)
    graph.add_node("analyst", analyst)
    graph.add_node("writer", writer)
    graph.add_node("reviewer", reviewer)
    graph.add_node("finalize", finalize)
    # 사람 조직의 초안→검토→반영 과정과 같은 순서로 엣지를 연결합니다.
    graph.add_edge(START, "researcher")
    graph.add_edge("researcher", "analyst")
    graph.add_edge("analyst", "writer")
    graph.add_edge("writer", "reviewer")
    graph.add_edge("reviewer", "finalize")
    graph.add_edge("finalize", END)
    # 실행 가능한 확장 그래프로 컴파일합니다.
    return graph.compile()


def run_review_exercise(provider: str) -> ReviewTeamState:
    """실습문제 1 완성 그래프를 실행하고 최종 상태를 반환합니다."""

    # provider별 Reviewer 확장 그래프를 생성합니다.
    team = build_review_team(provider)
    # 확장 상태에 필요한 다섯 칸을 모두 초기화합니다.
    initial: ReviewTeamState = {
        "raw": load_competitor_text(), "analysis": "", "report": "", "review": "", "final": ""
    }
    # 마지막 누적 상태를 보관합니다.
    final_state = initial.copy()
    # stream을 한 번만 실행해 중복 비용을 방지합니다.
    for current_state in team.stream(initial, stream_mode="values"):
        final_state = current_state
    # 검토 의견과 최종본이 포함된 최종 상태를 반환합니다.
    return final_state
