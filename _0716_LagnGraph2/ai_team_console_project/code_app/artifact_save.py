# -*- coding: utf-8 -*-
"""각 노드의 중간 산출물을 reports 폴더에 저장하는 래퍼 노드 실습입니다."""

# datetime은 실행마다 고유한 타임스탬프 파일명을 만들 때 사용합니다.
import datetime
# pathlib.Path는 텍스트 파일 저장 경로를 다룹니다.
from pathlib import Path

# 기본 상태와 노드 생성 함수, 데이터 로더를 재사용합니다.
from code_app.ai_team import TeamState, create_nodes, load_competitor_text
# 프로젝트 루트는 reports 폴더 위치를 정할 때 사용합니다.
from code_app.common_bridge import PROJECT_ROOT
# StateGraph로 저장 래퍼 노드의 실행 순서를 선언합니다.
from langgraph.graph import END, START, StateGraph

# 모든 실행 산출물을 프로젝트의 reports 폴더에 모읍니다.
REPORTS_DIR = PROJECT_ROOT / "reports"


def save_artifact(name: str, content: str, extension: str = "md") -> Path:
    """한 산출물을 UTF-8 파일로 저장하고 생성된 경로를 반환합니다."""

    # 폴더가 없으면 상위 폴더까지 만들고 이미 존재하면 오류 없이 넘어갑니다.
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    # 마이크로초까지 포함해 같은 초에 여러 파일을 만들어도 이름이 겹치지 않게 합니다.
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    # 단계명과 확장자를 조합해 실제 저장 경로를 만듭니다.
    output_path = REPORTS_DIR / f"{stamp}_{name}.{extension}"
    # 한글이 깨지지 않도록 UTF-8 인코딩을 지정해 파일을 기록합니다.
    output_path.write_text(content, encoding="utf-8")
    # 사용자가 저장 결과를 바로 확인할 수 있도록 경로를 출력합니다.
    print(f"  [저장] {name} → {output_path}")
    # 테스트나 후속 처리에서 사용할 수 있도록 경로를 반환합니다.
    return output_path


def build_saving_team(provider: str):
    """기본 세 노드를 감싸 실행 직후 각 산출물을 파일로 저장합니다."""

    # 선택한 provider를 사용하는 원래 노드 함수를 생성합니다.
    researcher, analyst, writer = create_nodes(provider)

    def researcher_save(state: TeamState) -> dict[str, str]:
        """Researcher 결과를 텍스트 파일로 저장합니다."""
        # 원래 노드를 실행해 부분 상태를 받습니다.
        update = researcher(state)
        # 정리된 사실을 txt 형식으로 저장합니다.
        save_artifact("01_research", update["raw"], "txt")
        # LangGraph 병합을 위해 원래 부분 상태를 그대로 반환합니다.
        return update

    def analyst_save(state: TeamState) -> dict[str, str]:
        """Analyst 결과를 마크다운 파일로 저장합니다."""
        # 원래 Analyst 노드를 실행합니다.
        update = analyst(state)
        # 분석 결과를 md 파일로 저장합니다.
        save_artifact("02_analysis", update["analysis"])
        # 상태 병합을 위해 분석 업데이트를 반환합니다.
        return update

    def writer_save(state: TeamState) -> dict[str, str]:
        """Writer 최종 보고서를 마크다운 파일로 저장합니다."""
        # 원래 Writer 노드를 실행합니다.
        update = writer(state)
        # 최종 보고서를 md 파일로 저장합니다.
        save_artifact("03_report", update["report"])
        # 최종 report 업데이트를 반환합니다.
        return update

    # 기본 상태를 사용하는 그래프를 생성합니다.
    graph = StateGraph(TeamState)
    # 원본 노드 대신 저장 기능이 추가된 래퍼 노드를 등록합니다.
    graph.add_node("researcher", researcher_save)
    graph.add_node("analyst", analyst_save)
    graph.add_node("writer", writer_save)
    # 기본 파이프라인과 같은 순서로 노드를 연결합니다.
    graph.add_edge(START, "researcher")
    graph.add_edge("researcher", "analyst")
    graph.add_edge("analyst", "writer")
    graph.add_edge("writer", END)
    # 저장 기능이 포함된 실행 그래프를 반환합니다.
    return graph.compile()


def run_saving_team(provider: str) -> TeamState:
    """중간 산출물 저장 그래프를 한 번 실행합니다."""

    # 선택한 provider의 저장 그래프를 생성합니다.
    team = build_saving_team(provider)
    # 기본 공유 상태를 초기화합니다.
    initial: TeamState = {"raw": load_competitor_text(), "analysis": "", "report": ""}
    # 최종 상태 보관 변수를 초기화합니다.
    final_state = initial.copy()
    # API 호출을 중복하지 않도록 stream을 한 번만 순회합니다.
    for current_state in team.stream(initial, stream_mode="values"):
        final_state = current_state
    # 화면 출력과 테스트에 사용할 최종 상태를 반환합니다.
    return final_state
