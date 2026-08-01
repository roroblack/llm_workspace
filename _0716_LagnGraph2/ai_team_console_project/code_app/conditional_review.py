# -*- coding: utf-8 -*-
"""분석 품질을 검사하고 부족하면 재조사·재분석하는 조건부 StateGraph 실습입니다."""

# TypedDict 확장을 위해 기존 TeamState를 상속합니다.
from code_app.ai_team import TeamState as BaseTeamState
# 기본 데이터 로더와 선택형 노드 생성 함수를 재사용합니다.
from code_app.ai_team import create_nodes, load_competitor_text
# StateGraph와 시작·종료 상수를 사용해 분기와 루프를 선언합니다.
from langgraph.graph import END, START, StateGraph

# 분석 재시도는 최대 두 번까지만 허용해 무한루프를 막습니다.
MAX_RETRIES = 2


class ConditionalTeamState(BaseTeamState):
    """기본 상태에 품질 판정과 재시도 횟수를 추가한 상태입니다."""

    # retries는 재조사 노드를 실행한 횟수입니다.
    retries: int
    # verdict는 check 노드가 만든 '충분' 또는 '부실' 판정입니다.
    verdict: str


def check(state: ConditionalTeamState) -> dict[str, str]:
    """분석 길이와 핵심 키워드를 기준으로 품질을 빠르게 검사합니다."""

    # 상태에 analysis가 없을 가능성까지 고려해 기본값을 빈 문자열로 가져옵니다.
    analysis = state.get("analysis", "")
    # 200자보다 짧으면 충분한 비교 분석이 아닐 가능성이 높다고 판단합니다.
    too_short = len(analysis) < 200
    # 강점·약점·기회 중 어느 표현도 없으면 핵심 분석 요소가 빠진 것으로 봅니다.
    missing_core = not any(keyword in analysis for keyword in ("강점", "약점", "기회"))
    # 두 조건 중 하나라도 참이면 부실, 모두 거짓이면 충분으로 판정합니다.
    verdict = "부실" if too_short or missing_core else "충분"
    # 분기 판단 근거를 콘솔에서 확인할 수 있도록 출력합니다.
    print(f"  [검수] 길이={len(analysis)}자 / 핵심키워드={'없음' if missing_core else '있음'} / {verdict}")
    # verdict 칸만 갱신하도록 부분 상태를 반환합니다.
    return {"verdict": verdict}


def route_after_check(state: ConditionalTeamState) -> str:
    """품질과 재시도 횟수에 따라 redo 또는 ok 경로 이름을 반환합니다."""

    # 분석이 부실하고 아직 최대 횟수에 도달하지 않았을 때만 재조사합니다.
    if state["verdict"] == "부실" and state["retries"] < MAX_RETRIES:
        return "redo"
    # 충분하거나 재시도 한도에 도달했으면 Writer로 진행합니다.
    return "ok"


def build_conditional_team(provider: str):
    """check 결과에 따라 redo 루프 또는 writer로 분기하는 그래프를 만듭니다."""

    # 선택한 provider용 기본 노드 세 개를 생성합니다.
    researcher, analyst, writer = create_nodes(provider)

    def redo(state: ConditionalTeamState) -> dict[str, object]:
        """기존 사실을 더 구체적으로 다시 정리하고 재시도 횟수를 증가시킵니다."""

        # 기본 Researcher를 다시 호출해 현재 raw를 더 정돈합니다.
        updated_raw = researcher(state)["raw"]
        # 현재 재시도 횟수에 1을 더해 다음 검사에서 상한을 판단하게 합니다.
        next_retry = state["retries"] + 1
        # 현재 몇 번째 재조사인지 사용자에게 알립니다.
        print(f"  [재조사] {next_retry}/{MAX_RETRIES}회")
        # raw와 retries 두 칸만 동시에 갱신합니다.
        return {"raw": updated_raw, "retries": next_retry}

    # 확장 상태를 사용하는 그래프를 생성합니다.
    graph = StateGraph(ConditionalTeamState)
    # 기본 세 노드와 품질 검사·재조사 노드를 등록합니다.
    graph.add_node("researcher", researcher)
    graph.add_node("analyst", analyst)
    graph.add_node("check", check)
    graph.add_node("redo", redo)
    graph.add_node("writer", writer)
    # 시작부터 분석 검사 전까지의 직선 흐름을 선언합니다.
    graph.add_edge(START, "researcher")
    graph.add_edge("researcher", "analyst")
    graph.add_edge("analyst", "check")
    # 라우터 반환값 redo/ok를 실제 redo/writer 노드에 매핑합니다.
    graph.add_conditional_edges("check", route_after_check, {"redo": "redo", "ok": "writer"})
    # 재조사가 끝나면 Analyst로 되돌아가는 루프 엣지를 선언합니다.
    graph.add_edge("redo", "analyst")
    # Writer 완료 후 그래프를 종료합니다.
    graph.add_edge("writer", END)
    # 실행 가능한 그래프로 컴파일해 반환합니다.
    return graph.compile()


def run_conditional_team(provider: str) -> ConditionalTeamState:
    """조건부 품질 재검토 그래프를 실행하고 최종 상태를 반환합니다."""

    # provider별 조건부 그래프를 생성합니다.
    team = build_conditional_team(provider)
    # 확장 상태의 모든 필드를 초기화합니다.
    initial: ConditionalTeamState = {
        "raw": load_competitor_text(), "analysis": "", "report": "", "retries": 0, "verdict": ""
    }
    # stream 마지막 값을 보관할 변수를 초기화합니다.
    final_state = initial.copy()
    # 그래프를 한 번만 실행하면서 각 노드 후의 누적 상태를 받습니다.
    for current_state in team.stream(initial, stream_mode="values"):
        final_state = current_state
    # 재실행 없이 최종 누적 상태를 반환합니다.
    return final_state
