# -*- coding: utf-8 -*-
"""ReAct, RAG, A2A, MCP 경로를 연결하는 LangGraph 워크플로우입니다."""

# 그래프 상태 구조를 선언하기 위해 TypedDict를 가져옵니다.
from typing import TypedDict
# 정규식으로 질문 속 월 정보를 추출하기 위해 re 모듈을 가져옵니다.
import re
# LangGraph의 시작, 종료, 상태 그래프 클래스를 가져옵니다.
from langgraph.graph import END, START, StateGraph
# ReAct 실행 함수를 가져옵니다.
from app.agents.react_agent import run_react
# A2A 전문 에이전트 호출 함수를 가져옵니다.
from app.a2a.specialists import invoke_specialist
# MCP 공유 도구를 가져옵니다.
from app.mcp_server.tools import mcp_csv_preview, mcp_data_summary, mcp_file_list, mcp_monthly_sales
# RAG 검색 서비스를 가져옵니다.
from app.services.rag_service import search_knowledge
# 모델 생성 및 응답 추출 함수를 가져옵니다.
from app.core.common import get_chat
from app.services.message_utils import extract_text
# 현재 공급자를 ContextVar에 저장하는 함수를 가져옵니다.
from app.services.provider_context import set_provider


class WorkflowState(TypedDict, total=False):
    """LangGraph 노드들이 공유하는 상태 필드를 정의합니다."""
    message: str
    provider: str
    thread_id: str
    route: str
    target_agent: str
    answer: str
    sources: list[dict[str, object]]
    trace: list[dict[str, str]]


def _trace(state: WorkflowState, stage: str, detail: str) -> list[dict[str, str]]:
    """기존 실행 추적에 새 단계를 추가한 목록을 반환합니다."""
    # 기존 trace가 없을 때 빈 목록을 사용합니다.
    trace = list(state.get("trace", []))
    # 현재 단계와 설명을 새 항목으로 추가합니다.
    trace.append({"stage": stage, "detail": detail})
    # 갱신된 추적 목록을 반환합니다.
    return trace


def classify_node(state: WorkflowState) -> WorkflowState:
    """질문의 핵심 의도에 따라 다음 실행 경로를 결정합니다."""
    # 공급자를 현재 요청 컨텍스트에 저장합니다.
    set_provider(state["provider"])
    # 분류 비교를 위해 질문 문자열을 소문자로 변환합니다.
    message = state["message"].lower()
    # mcp: 접두어는 MCP 도구 직접 실행으로 분류합니다.
    if message.startswith("mcp:"):
        route, target = "mcp", "monthly_sales"
    # 정책, 매뉴얼, 내부 근거 질문은 RAG 경로로 분류합니다.
    elif any(keyword in message for keyword in ["정책", "매뉴얼", "핸드북", "근거", "rag"]):
        route, target = "rag", "knowledge-agent"
    # 보고서나 차트 생성 요청은 보고서 전문 에이전트로 위임합니다.
    elif any(keyword in message for keyword in ["보고서", "리포트", "차트", "그래프"]):
        route, target = "a2a", "report-writer-agent"
    # 매출이나 성장률의 단순 수치 분석은 매출 전문 에이전트로 위임합니다.
    elif any(keyword in message for keyword in ["매출", "성장률", "카테고리", "전월"]):
        route, target = "a2a", "sales-analyst-agent"
    # 전략, 마케팅, 제언 요청은 전략 전문 에이전트로 위임합니다.
    elif any(keyword in message for keyword in ["전략", "마케팅", "제언", "개선"]):
        route, target = "a2a", "strategy-agent"
    # 여러 데이터와 도구 판단이 필요한 일반 질문은 ReAct로 보냅니다.
    else:
        route, target = "react", "react-agent"
    # 선택된 경로와 추적 정보를 상태에 추가합니다.
    return {**state, "route": route, "target_agent": target, "trace": _trace(state, "LangGraph", f"route={route}, target={target}")}


def rag_node(state: WorkflowState) -> WorkflowState:
    """RAG 근거를 검색하고 근거 고정 답변을 생성합니다."""
    # 질문과 유사한 문서 근거를 검색합니다.
    rag = search_knowledge(state["message"], state["provider"])
    # 공급자별 채팅 모델을 생성합니다.
    llm = get_chat(provider=state["provider"], temperature=0.1)
    # 검색 근거 밖의 내용을 만들지 못하도록 제한한 프롬프트를 구성합니다.
    prompt = f"아래 내부 근거만 사용해 답하라. 근거에 없으면 확인할 수 없다고 답하라.\n질문: {state['message']}\n\n{rag['context']}"
    # 모델을 호출해 답변을 생성합니다.
    answer = extract_text(llm.invoke(prompt))
    # 답변, 출처, 실행 추적을 상태에 추가합니다.
    return {**state, "answer": answer, "sources": rag["sources"], "trace": _trace(state, "RAG", f"근거 {len(rag['sources'])}개 검색")}


def a2a_node(state: WorkflowState) -> WorkflowState:
    """선택된 전문 에이전트에 질문을 위임합니다."""
    # 분류 단계에서 정한 전문 에이전트를 호출합니다.
    result = invoke_specialist(state["target_agent"], state["message"], state["provider"])
    # 전문 에이전트 응답을 현재 상태에 병합합니다.
    return {**state, "answer": str(result.get("answer", "")), "sources": result.get("sources", []), "trace": _trace(state, "A2A", f"{state['target_agent']} 위임 완료")}


def mcp_node(state: WorkflowState) -> WorkflowState:
    """FastAPI 프로세스 내부에서 MCP와 동일한 순수 도구 함수를 실행합니다."""
    # 접두어 뒤의 명령 문자열을 추출합니다.
    command = state["message"][4:].strip()
    # data 또는 files 명령은 전체 파일 목록을 반환합니다.
    if command.startswith("files"):
        answer = mcp_file_list()
    # summary 명령은 핵심 데이터 요약을 반환합니다.
    elif command.startswith("summary"):
        answer = mcp_data_summary()
    # csv 명령은 'csv 파일명' 형식에서 파일명을 추출합니다.
    elif command.startswith("csv"):
        parts = command.split(maxsplit=1)
        answer = mcp_csv_preview(parts[1] if len(parts) > 1 else "monthly_sales.csv")
    # 그 밖의 경우 질문에서 YYYY-MM을 찾아 월별 매출을 조회합니다.
    else:
        match = re.search(r"\b(20\d{2}-\d{2})\b", command)
        answer = mcp_monthly_sales(match.group(1) if match else "")
    # MCP 도구 실행 결과와 추적 정보를 상태에 추가합니다.
    return {**state, "answer": answer, "trace": _trace(state, "MCP", "공유 MCP 도구 실행 완료")}


def react_node(state: WorkflowState) -> WorkflowState:
    """ReAct 에이전트가 필요한 도구를 자율 선택하도록 실행합니다."""
    # 질문, 공급자, 대화 스레드를 전달해 ReAct 루프를 실행합니다.
    answer = run_react(state["message"], state["provider"], state["thread_id"])
    # 최종 답변과 실행 추적을 상태에 추가합니다.
    return {**state, "answer": answer, "trace": _trace(state, "ReAct", "도구 선택 및 관찰 루프 완료")}


def route_after_classify(state: WorkflowState) -> str:
    """분류 노드의 route 값을 다음 노드 이름으로 반환합니다."""
    # 상태에 기록된 경로 문자열을 그대로 반환합니다.
    return state["route"]


def build_workflow():
    """전체 Business Agent LangGraph 실행 객체를 생성합니다."""
    # WorkflowState를 공유 상태로 사용하는 그래프 빌더를 생성합니다.
    graph = StateGraph(WorkflowState)
    # 각 실행 함수를 그래프 노드로 등록합니다.
    graph.add_node("classify", classify_node)
    graph.add_node("rag", rag_node)
    graph.add_node("a2a", a2a_node)
    graph.add_node("mcp", mcp_node)
    graph.add_node("react", react_node)
    # 시작점에서 항상 분류 노드로 이동하도록 연결합니다.
    graph.add_edge(START, "classify")
    # 분류 결과에 따라 네 경로 중 하나를 선택하도록 조건부 간선을 추가합니다.
    graph.add_conditional_edges("classify", route_after_classify, {"rag": "rag", "a2a": "a2a", "mcp": "mcp", "react": "react"})
    # 각 처리 노드는 답변 생성 후 그래프를 종료하도록 연결합니다.
    graph.add_edge("rag", END)
    graph.add_edge("a2a", END)
    graph.add_edge("mcp", END)
    graph.add_edge("react", END)
    # 실행 가능한 그래프로 컴파일해 반환합니다.
    return graph.compile()

# 애플리케이션 전체에서 재사용할 컴파일된 그래프를 한 번 생성합니다.
workflow = build_workflow()
