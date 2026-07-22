# -*- coding: utf-8 -*-
"""ReAct, RAG, A2A, MCP를 LangGraph 상태 그래프로 연결하는 핵심 워크플로우입니다."""

# operator.add는 노드별 trace 목록을 누적하는 리듀서로 사용합니다.
import operator
# re는 사용자 질문에서 주문번호를 추출할 때 사용합니다.
import re
# time은 재시도 사이의 지수 백오프 대기에 사용합니다.
import time
# typing의 Annotated는 LangGraph 상태 필드에 리듀서를 연결합니다.
from typing import Annotated, Literal, TypedDict

# END와 START는 LangGraph 그래프의 시작과 종료 지점을 나타냅니다.
from langgraph.graph import END, START, StateGraph

# ReAct 전문 에이전트 호출 함수를 가져옵니다.
from app.agents.react_agent import invoke_react_agent
# A2A 위임 함수를 가져옵니다.
from app.agents.specialists import delegate_to_agent
# 환경설정과 로거를 가져옵니다.
from app.core.logging_config import setup_logging
from app.core.settings import get_settings
# 로컬 MCP 클라이언트 추상화를 가져옵니다.
from app.mcp_server.client import call_local_mcp_tool
# 정책 RAG 직접 검색 함수를 가져옵니다.
from app.services.rag_service import search_policy

# 공용 로거를 모듈 로드 시 한 번 초기화합니다.
logger = setup_logging()


# WorkflowState는 그래프 노드 사이에 전달되는 상태 구조입니다.
class WorkflowState(TypedDict, total=False):
    """통합 에이전트 워크플로우에서 공유하는 상태입니다."""

    # message는 사용자가 입력한 원문 질문입니다.
    message: str
    # thread_id는 메모리 세션 식별자입니다.
    thread_id: str
    # provider는 OpenAI 또는 Gemini 공급자입니다.
    provider: Literal["openai", "gemini"]
    # route는 분류 노드가 선택한 처리 경로입니다.
    route: str
    # target_agent는 A2A 위임 대상 전문 에이전트입니다.
    target_agent: str
    # context는 RAG 또는 MCP에서 수집한 근거입니다.
    context: str
    # answer는 최종 사용자 답변입니다.
    answer: str
    # error는 실행 중 발생한 오류 메시지입니다.
    error: str
    # trace는 노드 실행 정보를 누적합니다.
    trace: Annotated[list[dict[str, object]], operator.add]


# _trace 함수는 일관된 단계 추적 딕셔너리를 만듭니다.
def _trace(stage: str, detail: str) -> list[dict[str, object]]:
    """LangGraph 응답에 포함할 단계 추적 레코드를 생성합니다."""
    # 단계 이름과 세부 설명을 하나의 원소 리스트로 반환합니다.
    return [{"stage": stage, "detail": detail}]


# classify_node는 질문 유형을 결정합니다.
def classify_node(state: WorkflowState) -> WorkflowState:
    """키워드 기반의 결정적 라우팅으로 첫 처리 경로를 선택합니다."""
    # 질문을 소문자로 변환하고 공백을 제거합니다.
    message = state["message"].strip().lower()
    # 교환을 실제로 요청하는 질문은 A2A 교환 에이전트로 보냅니다.
    if any(keyword in message for keyword in ["교환 신청", "교환하고", "교환 접수"]):
        # 쓰기 작업은 전문 에이전트에 위임합니다.
        return {"route": "a2a", "target_agent": "exchange-agent", "trace": _trace("LangGraph", "교환 쓰기 작업을 A2A 경로로 분류")}
    # 환불, 정책, 멤버십 질문은 RAG 경로로 보냅니다.
    if any(keyword in message for keyword in ["정책", "환불", "멤버십", "반품"]):
        # 정책 근거를 먼저 검색하도록 지정합니다.
        return {"route": "rag", "target_agent": "policy-agent", "trace": _trace("LangGraph", "정책 질문을 RAG 경로로 분류")}
    # 주문번호가 포함되면 MCP 주문 도구를 직접 사용합니다.
    if re.search(r"\b[oO]\d{6}\b", message):
        # 표준 도구 호출 계층인 MCP 경로를 선택합니다.
        return {"route": "mcp", "target_agent": "order-agent", "trace": _trace("LangGraph", "주문번호 질문을 MCP 경로로 분류")}
    # 재고 관련 키워드는 A2A 재고 에이전트로 보냅니다.
    if any(keyword in message for keyword in ["재고", "남아", "있어"]):
        # 전문 에이전트 위임 경로를 선택합니다.
        return {"route": "a2a", "target_agent": "inventory-agent", "trace": _trace("LangGraph", "재고 질문을 A2A 경로로 분류")}
    # 그 밖의 복합 질문은 ReAct가 도구를 자율 선택하도록 합니다.
    return {"route": "react", "trace": _trace("LangGraph", "복합 질문을 ReAct 경로로 분류")}


# rag_node는 정책 문서 근거를 직접 검색합니다.
def rag_node(state: WorkflowState) -> WorkflowState:
    """RAG 단계에서 정책 PDF 근거 청크를 수집합니다."""
    # 선택된 공급자 임베딩으로 정책 검색을 실행합니다.
    context = search_policy(state["message"], state["provider"])
    # 검색 근거와 단계 추적을 상태에 저장합니다.
    return {"context": context, "trace": _trace("RAG", "정책 PDF에서 관련 근거 청크 검색 완료")}


# a2a_node는 역할별 전문 에이전트에 작업을 위임합니다.
def a2a_node(state: WorkflowState) -> WorkflowState:
    """A2A 게이트웨이를 통해 전문 에이전트 결과를 받습니다."""
    # 분류된 대상 에이전트에 질문을 위임합니다.
    answer = delegate_to_agent(state["target_agent"], state["message"], state["provider"])
    # 전문 에이전트의 결과를 최종 답변 후보로 저장합니다.
    return {"answer": answer, "trace": _trace("A2A", f"{state['target_agent']}에 작업 위임 완료")}


# mcp_node는 MCP 도구 호출 인터페이스를 통해 주문 도구를 실행합니다.
def mcp_node(state: WorkflowState) -> WorkflowState:
    """MCP 클라이언트 계층으로 표준화된 도구 호출을 실행합니다."""
    # 질문에서 주문번호를 추출합니다.
    match = re.search(r"\b[oO]\d{6}\b", state["message"])
    # 주문번호가 없으면 도구 인자를 받을 수 없으므로 명확화 응답을 만듭니다.
    if match is None:
        # 잘못된 입력을 임의 추정하지 않습니다.
        return {"answer": "주문번호를 O000000 형식으로 입력해 주세요.", "trace": _trace("MCP", "주문번호 누락으로 도구 호출 중단")}
    # 로컬 MCP 클라이언트 추상화로 주문 도구를 실행합니다.
    result = call_local_mcp_tool("get_order_status", {"order_id": match.group(0).upper()})
    # MCP 도구 결과를 최종 답변 후보로 저장합니다.
    return {"answer": result, "trace": _trace("MCP", "get_order_status 도구 호출 완료")}


# react_node는 자율 도구 선택이 필요한 질문을 ReAct 에이전트로 처리합니다.
def react_node(state: WorkflowState) -> WorkflowState:
    """최신 LangChain create_agent 기반 ReAct 루프를 실행합니다."""
    # ReAct 에이전트에 질문과 메모리 세션을 전달합니다.
    answer = invoke_react_agent(state["message"], state["thread_id"], state["provider"])
    # 에이전트의 최종 답변을 상태에 저장합니다.
    return {"answer": answer, "trace": _trace("ReAct", "도구 선택·실행·관찰 루프 완료")}


# grounded_answer_node는 RAG 근거를 LLM이 읽기 쉬운 질문으로 재구성해 답변합니다.
def grounded_answer_node(state: WorkflowState) -> WorkflowState:
    """RAG 검색 결과만 근거로 최종 정책 답변을 생성합니다."""
    # 원 질문과 검색 근거를 ReAct 에이전트에 전달할 메시지로 조합합니다.
    grounded_message = (
        "다음 정책 문서 근거만 사용하여 질문에 답하세요. 근거에 없으면 모른다고 답하세요.\n\n"
        f"[사용자 질문]\n{state['message']}\n\n[검색 근거]\n{state.get('context', '')}"
    )
    # 기존 thread_id와 공급자로 답변 생성 단계를 실행합니다.
    answer = invoke_react_agent(grounded_message, state["thread_id"], state["provider"])
    # 최종 답변과 근거 고정 단계를 추적합니다.
    return {"answer": answer, "trace": _trace("Grounded Answer", "RAG 근거로만 정책 답변 생성 완료")}


# error_node는 모든 처리 실패를 사용자 친화적인 응답으로 바꿉니다.
def error_node(state: WorkflowState) -> WorkflowState:
    """그래프 오류 상태를 안전한 사용자 응답으로 변환합니다."""
    # 내부 상세 오류를 그대로 노출하지 않고 일반 안내를 제공합니다.
    answer = "요청 처리 중 오류가 발생했습니다. API 키, 네트워크, 데이터 파일을 확인해 주세요."
    # 오류 내용은 추적 정보에 남겨 개발자가 확인할 수 있게 합니다.
    return {"answer": answer, "trace": _trace("Error", state.get("error", "알 수 없는 오류"))}


# _route_after_classify 함수는 분류 결과에 맞는 다음 노드를 반환합니다.
def _route_after_classify(state: WorkflowState) -> str:
    """route 상태값을 LangGraph 노드 이름으로 변환합니다."""
    # 저장된 route 값을 그대로 반환합니다.
    return state["route"]


# _build_graph 함수는 노드와 간선을 연결해 컴파일된 그래프를 만듭니다.
def _build_graph():
    """통합 처리 흐름을 StateGraph로 선언하고 컴파일합니다."""
    # WorkflowState 타입을 사용하는 그래프 빌더를 생성합니다.
    graph = StateGraph(WorkflowState)
    # 질문 분류 노드를 등록합니다.
    graph.add_node("classify", classify_node)
    # RAG 검색 노드를 등록합니다.
    graph.add_node("rag", rag_node)
    # A2A 위임 노드를 등록합니다.
    graph.add_node("a2a", a2a_node)
    # MCP 도구 호출 노드를 등록합니다.
    graph.add_node("mcp", mcp_node)
    # ReAct 자율 처리 노드를 등록합니다.
    graph.add_node("react", react_node)
    # RAG 근거 답변 생성 노드를 등록합니다.
    graph.add_node("grounded_answer", grounded_answer_node)
    # 오류 응답 노드를 등록합니다.
    graph.add_node("error", error_node)
    # 시작점에서 분류 노드로 연결합니다.
    graph.add_edge(START, "classify")
    # 분류 결과에 따라 네 경로 중 하나로 조건 분기합니다.
    graph.add_conditional_edges(
        "classify",
        _route_after_classify,
        {"rag": "rag", "a2a": "a2a", "mcp": "mcp", "react": "react"},
    )
    # RAG 검색 후에는 근거 기반 답변 생성으로 연결합니다.
    graph.add_edge("rag", "grounded_answer")
    # 각 최종 처리 노드를 그래프 종료점과 연결합니다.
    graph.add_edge("grounded_answer", END)
    # A2A 결과는 바로 종료합니다.
    graph.add_edge("a2a", END)
    # MCP 결과는 바로 종료합니다.
    graph.add_edge("mcp", END)
    # ReAct 결과는 바로 종료합니다.
    graph.add_edge("react", END)
    # 완성된 그래프를 실행 가능한 객체로 컴파일합니다.
    return graph.compile()


# _workflow는 모듈 로드 시 한 번 컴파일하여 요청마다 재사용합니다.
_workflow = _build_graph()


# run_workflow 함수는 재시도와 지수 백오프를 포함해 그래프를 실행합니다.
def run_workflow(message: str, thread_id: str, provider: Literal["openai", "gemini"]) -> WorkflowState:
    """통합 LangGraph를 실행하고 최종 상태를 반환합니다."""
    # 환경설정에서 재시도 횟수와 대기 기준값을 읽습니다.
    settings = get_settings()
    # 마지막 오류를 저장할 변수를 초기화합니다.
    last_error = ""
    # 설정한 최대 횟수만큼 그래프 실행을 시도합니다.
    for attempt in range(1, settings.max_retries + 1):
        # 네트워크 또는 모델 오류를 처리하기 위해 try-except를 사용합니다.
        try:
            # 그래프 초기 상태를 구성하여 실행합니다.
            result = _workflow.invoke(
                {
                    "message": message,
                    "thread_id": thread_id,
                    "provider": provider,
                    "trace": _trace("Start", f"요청 시작: attempt={attempt}"),
                }
            )
            # 성공한 최종 상태를 반환합니다.
            return result
        except Exception as exc:
            # 예외 메시지를 개발용 변수에 저장합니다.
            last_error = f"{type(exc).__name__}: {exc}"
            # 실패 정보를 구조적 로그에 남깁니다.
            logger.exception("워크플로우 실행 실패: attempt=%s", attempt)
            # 마지막 시도가 아니면 지수 백오프 후 다시 시도합니다.
            if attempt < settings.max_retries:
                # 대기 시간은 base * 2^(시도-1) 공식으로 증가합니다.
                delay = settings.retry_base_seconds * (2 ** (attempt - 1))
                # 계산된 시간만큼 현재 요청 스레드를 대기시킵니다.
                time.sleep(delay)
    # 모든 시도가 실패하면 오류 노드를 직접 호출해 안전한 응답을 만듭니다.
    return error_node({"error": last_error, "trace": _trace("Retry", "모든 재시도 소진")})
