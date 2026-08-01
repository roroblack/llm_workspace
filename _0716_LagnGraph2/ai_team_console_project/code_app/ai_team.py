# -*- coding: utf-8 -*-
"""ai_team.py를 기반으로 OpenAI/Gemini 선택이 가능하도록 확장한 핵심 모듈입니다."""

# Callable은 노드 함수의 타입을 명확히 표현할 때 사용합니다.
from collections.abc import Callable
# TypedDict는 LangGraph에서 공유할 상태 딕셔너리의 키와 타입을 선언합니다.
from typing import TypedDict

# pandas는 제공된 competitor_data.csv 파일을 읽습니다.
import pandas as pd
# HumanMessage와 SystemMessage는 LLM에 역할 지시와 실제 입력을 구분해 전달합니다.
from langchain_core.messages import HumanMessage, SystemMessage
# START와 END는 그래프의 시작·종료점이고 StateGraph는 노드와 엣지를 선언합니다.
from langgraph.graph import END, START, StateGraph

# 제공된 common.py의 DATA와 get_chat을 수정 없이 사용합니다.
from code_app.common_bridge import DATA, get_chat


class TeamState(TypedDict):
    """Researcher, Analyst, Writer가 함께 사용하는 공유 상태의 기본 구조입니다."""

    # raw는 최초에는 CSV 원문 텍스트이고 Researcher 실행 후에는 정리된 사실이 됩니다.
    raw: str
    # analysis는 Analyst가 정리된 사실을 바탕으로 만든 경쟁사 분석입니다.
    analysis: str
    # report는 Writer가 분석 결과로 작성한 최종 마크다운 보고서입니다.
    report: str


def load_competitor_text() -> str:
    """제공된 경쟁사 CSV를 읽어 LLM이 이해하기 쉬운 불릿 텍스트로 변환합니다."""

    # common.py의 DATA 경로 아래에서 원본 CSV 파일을 읽습니다.
    csv_path = DATA / "competitor_data.csv"
    # 필수 데이터가 없을 때 원인을 바로 알 수 있도록 명확한 예외를 발생시킵니다.
    if not csv_path.exists():
        raise FileNotFoundError(f"경쟁사 데이터 파일을 찾을 수 없습니다: {csv_path}")
    # CSV의 각 열을 유지한 채 pandas DataFrame으로 불러옵니다.
    dataframe = pd.read_csv(csv_path)
    # 각 행을 LLM이 읽기 쉬운 한 줄 설명으로 변환해 리스트에 저장합니다.
    lines = [
        # itertuples의 각 행에서 회사명, 주력 분야, 평점, 강점, 약점을 꺼냅니다.
        f"- {row.company}: 주력={row.main_category}, 평점={row.rating}, "
        f"강점={row.strength}, 약점={row.weakness}"
        for row in dataframe.itertuples()
    ]
    # 제목과 모든 경쟁사 행을 줄바꿈으로 연결해 하나의 입력 문자열로 반환합니다.
    return "승승장구몰 경쟁사 현황:\n" + "\n".join(lines)


def create_nodes(provider: str, temperature: float = 0.2) -> tuple[Callable, Callable, Callable]:
    """선택한 provider의 LLM을 사용하는 Researcher·Analyst·Writer 노드를 생성합니다."""

    # common.py의 get_chat에 openai 또는 gemini를 전달해 해당 모델 객체를 생성합니다.
    llm = get_chat(provider=provider, temperature=temperature)

    def researcher(state: TeamState) -> dict[str, str]:
        """원천 데이터를 해석하지 않고 사실 중심으로 정리합니다."""

        # 시스템 메시지로 Researcher가 분석이나 추측을 하지 않도록 역할을 제한합니다.
        system = SystemMessage(
            "너는 리서처다. 주어진 데이터를 해석 없이 사실만 항목별로 정리하라. "
            "회사명, 주력 카테고리, 평점, 강점, 약점을 빠뜨리지 마라."
        )
        # 최초 상태의 raw에 들어 있는 경쟁사 원천 텍스트를 사용자 메시지로 전달합니다.
        human = HumanMessage(f"[경쟁사 원천 데이터]\n{state['raw']}")
        # LLM을 한 번 호출하고 반환 메시지의 본문을 문자열로 꺼냅니다.
        output = llm.invoke([system, human]).content
        # LangGraph가 기존 상태에 병합할 raw 칸만 반환합니다.
        return {"raw": str(output)}

    def analyst(state: TeamState) -> dict[str, str]:
        """Researcher가 정리한 사실만 사용해 경쟁사별 강점·약점·기회를 분석합니다."""

        # 시스템 메시지로 분석 범위와 반드시 포함할 분석 항목을 지정합니다.
        system = SystemMessage(
            "너는 시장 분석가다. 정리된 사실만 근거로 경쟁사별 강점과 약점을 비교하고, "
            "승승장구몰의 시장 기회와 대응 전략을 구체적으로 분석하라."
        )
        # 앞 단계가 갱신한 raw 값만 Analyst의 입력으로 전달합니다.
        human = HumanMessage(f"[Researcher가 정리한 사실]\n{state['raw']}")
        # 분석 모델을 호출해 메시지 본문을 가져옵니다.
        output = llm.invoke([system, human]).content
        # 공유 상태에서 analysis 칸만 갱신하도록 부분 딕셔너리를 반환합니다.
        return {"analysis": str(output)}

    def writer(state: TeamState) -> dict[str, str]:
        """Analyst의 분석만 사용해 임원 보고용 마크다운 리포트를 작성합니다."""

        # 시스템 메시지로 보고서 역할과 문서 구성을 고정합니다.
        system = SystemMessage(
            "너는 임원 보고서 작성자다. 분석 결과를 근거로 마크다운 보고서를 작성하라. "
            "제목, 핵심 요약, 경쟁사별 비교, 기회, 실행 제언 순서를 지켜라."
        )
        # 앞 단계가 만든 analysis 값만 Writer 입력으로 전달해 역할 간 결합을 낮춥니다.
        human = HumanMessage(f"[Analyst 분석 결과]\n{state['analysis']}")
        # Writer 역할의 LLM 호출 결과에서 텍스트 본문을 꺼냅니다.
        output = llm.invoke([system, human]).content
        # 최종 산출물인 report 칸만 갱신하도록 반환합니다.
        return {"report": str(output)}

    # 세 노드 함수를 그래프 조립 코드가 사용할 수 있도록 튜플로 반환합니다.
    return researcher, analyst, writer


def build_team(provider: str):
    """START → Researcher → Analyst → Writer → END 순서의 StateGraph를 만듭니다."""

    # 선택한 모델 공급자를 사용하는 세 노드를 생성합니다.
    researcher, analyst, writer = create_nodes(provider)
    # TeamState의 구조를 공유 상태 계약으로 사용하는 그래프 빌더를 생성합니다.
    graph = StateGraph(TeamState)
    # 각 Python 함수를 식별 가능한 노드 이름과 함께 그래프에 등록합니다.
    graph.add_node("researcher", researcher)
    graph.add_node("analyst", analyst)
    graph.add_node("writer", writer)
    # 그래프 시작점에서 Researcher로 이동하도록 첫 엣지를 선언합니다.
    graph.add_edge(START, "researcher")
    # Researcher 완료 후 Analyst가 실행되도록 연결합니다.
    graph.add_edge("researcher", "analyst")
    # Analyst 완료 후 Writer가 실행되도록 연결합니다.
    graph.add_edge("analyst", "writer")
    # Writer가 보고서를 만들면 그래프를 종료하도록 연결합니다.
    graph.add_edge("writer", END)
    # 선언한 그래프를 실제 invoke/stream이 가능한 실행 객체로 컴파일합니다.
    return graph.compile()


def run_basic_team(provider: str, show_progress: bool = True) -> TeamState:
    """기본 AI 팀을 한 번 실행하고 누적된 최종 상태를 반환합니다."""

    # provider에 맞는 기본 파이프라인을 컴파일합니다.
    team = build_team(provider)
    # raw에는 원천 텍스트를 넣고 아직 생성되지 않은 나머지 칸은 빈 문자열로 둡니다.
    initial: TeamState = {"raw": load_competitor_text(), "analysis": "", "report": ""}
    # 그래프가 아직 실행되지 않았을 때도 반환할 상태가 있도록 초기 상태를 복사합니다.
    final_state: TeamState = initial.copy()
    # values 모드는 각 노드 후의 누적 상태를 반환하므로 진행과 최종 결과를 한 번에 얻습니다.
    for current_state in team.stream(initial, stream_mode="values"):
        # 마지막 반복의 누적 상태가 전체 파이프라인의 최종 상태가 됩니다.
        final_state = current_state
        # 메뉴 실행일 때만 어떤 단계가 완료됐는지 화면에 표시합니다.
        if show_progress:
            completed = []
            # 분석 결과가 존재하면 Analyst 단계 완료로 표시합니다.
            if current_state.get("analysis"):
                completed.append("analysis")
            # 보고서가 존재하면 Writer 단계 완료로 표시합니다.
            if current_state.get("report"):
                completed.append("report")
            # 완료 목록이 비어 있으면 Researcher가 동작 중인 시작 단계로 표시합니다.
            print(f"  [진행] {', '.join(completed) if completed else 'researcher'}")
    # API를 다시 호출하지 않고 stream에서 얻은 마지막 상태를 반환합니다.
    return final_state
