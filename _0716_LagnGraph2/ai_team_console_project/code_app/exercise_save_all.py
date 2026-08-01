# -*- coding: utf-8 -*-
"""실습문제 2 해답: Research·Analysis·Report·Final 네 산출물을 output 폴더에 저장합니다."""

# 프로젝트 루트는 output 폴더의 절대 경로를 정할 때 사용합니다.
from code_app.common_bridge import PROJECT_ROOT
# 실습문제 1의 상태와 그래프 구성을 재사용할 수 있는 구성 요소를 가져옵니다.
from code_app.ai_team import create_nodes, load_competitor_text
from code_app.exercise_reviewer import ReviewTeamState
# Reviewer와 Finalize를 이 파일 안에서 provider별로 생성하기 위해 메시지 클래스를 사용합니다.
from code_app.common_bridge import get_chat
from langchain_core.messages import HumanMessage, SystemMessage
# 모든 저장 래퍼 노드를 StateGraph에 연결합니다.
from langgraph.graph import END, START, StateGraph

# 실습문제 요구사항대로 고정 파일 네 개를 output 폴더에 생성합니다.
OUTPUT_DIR = PROJECT_ROOT / "output"


def save(name: str, content: str) -> None:
    """output 폴더 아래에 지정한 이름으로 UTF-8 텍스트를 저장합니다."""

    # output 폴더가 없으면 자동으로 생성합니다.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # 프로젝트 루트와 파일명을 결합해 저장 경로를 만듭니다.
    output_path = OUTPUT_DIR / name
    # 한글과 마크다운이 깨지지 않도록 UTF-8로 기록합니다.
    output_path.write_text(content, encoding="utf-8")
    # 파일명과 글자 수를 표시해 저장 성공을 확인하게 합니다.
    print(f"  [저장] {name} ({len(content)}자)")


def build_save_all_team(provider: str):
    """실습문제 1의 전체 흐름에 네 단계 파일 저장을 결합합니다."""

    # 선택한 provider로 Researcher·Analyst·Writer를 생성합니다.
    researcher, analyst, writer = create_nodes(provider)
    # Reviewer와 Finalize도 같은 provider를 사용하도록 모델을 생성합니다.
    llm = get_chat(provider=provider, temperature=0.2)

    def researcher_save(state: ReviewTeamState) -> dict[str, str]:
        """정리된 사실을 research.md로 저장합니다."""
        update = researcher(state)
        save("research.md", update["raw"])
        return update

    def analyst_save(state: ReviewTeamState) -> dict[str, str]:
        """분석 결과를 analysis.md로 저장합니다."""
        update = analyst(state)
        save("analysis.md", update["analysis"])
        return update

    def writer_save(state: ReviewTeamState) -> dict[str, str]:
        """Writer 초안을 report.md로 저장합니다."""
        update = writer(state)
        save("report.md", update["report"])
        return update

    def reviewer(state: ReviewTeamState) -> dict[str, str]:
        """Writer 초안의 개선 의견을 review 칸에 저장합니다."""
        output = llm.invoke([
            SystemMessage("너는 보고서 검토자다. 사실성·가독성·구성 개선점을 3가지 이내로 제시하라."),
            HumanMessage(f"[검토할 리포트]\n{state['report']}"),
        ]).content
        return {"review": str(output)}

    def finalize_save(state: ReviewTeamState) -> dict[str, str]:
        """검토 의견을 반영한 최종본을 27_final.md로 저장합니다."""
        output = llm.invoke([
            SystemMessage("너는 최종 편집자다. 리포트에 검토 의견을 반영해 최종 마크다운 문서를 작성하라."),
            HumanMessage(f"[리포트]\n{state['report']}\n\n[검토 의견]\n{state['review']}"),
        ]).content
        update = {"final": str(output)}
        save("27_final.md", update["final"])
        return update

    # Reviewer 확장 상태를 사용하는 그래프를 생성합니다.
    graph = StateGraph(ReviewTeamState)
    # 각 단계에서 저장이 필요한 노드는 래퍼 함수로 등록합니다.
    graph.add_node("researcher", researcher_save)
    graph.add_node("analyst", analyst_save)
    graph.add_node("writer", writer_save)
    graph.add_node("reviewer", reviewer)
    graph.add_node("finalize", finalize_save)
    # 실습문제 1과 동일한 직렬 흐름을 선언합니다.
    graph.add_edge(START, "researcher")
    graph.add_edge("researcher", "analyst")
    graph.add_edge("analyst", "writer")
    graph.add_edge("writer", "reviewer")
    graph.add_edge("reviewer", "finalize")
    graph.add_edge("finalize", END)
    # 실행 가능한 저장 그래프로 컴파일합니다.
    return graph.compile()


def run_save_all_exercise(provider: str) -> ReviewTeamState:
    """실습문제 2 그래프를 실행하고 네 파일과 최종 상태를 만듭니다."""

    # 선택한 provider의 저장 그래프를 생성합니다.
    team = build_save_all_team(provider)
    # 모든 상태 칸을 초기화합니다.
    initial: ReviewTeamState = {
        "raw": load_competitor_text(), "analysis": "", "report": "", "review": "", "final": ""
    }
    # 마지막 상태를 담을 변수를 초기화합니다.
    final_state = initial.copy()
    # 그래프를 한 번만 실행해 모든 파일과 최종 결과를 생성합니다.
    for current_state in team.stream(initial, stream_mode="values"):
        final_state = current_state
    # 생성된 output 폴더 위치를 알려줍니다.
    print(f"\n완료 — {OUTPUT_DIR} 폴더를 확인하세요.")
    # 메뉴에서 최종본을 출력할 수 있도록 상태를 반환합니다.
    return final_state
