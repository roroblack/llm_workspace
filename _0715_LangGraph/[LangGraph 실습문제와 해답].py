[LangGraph 실습문제와 해답]

문제 1 — 긴급 알림 조건 분기 추가
TicketState에 alert 키를 추가하고 notify_node(긴급 티켓에 alert="즉시알림" 세팅)를 만든 뒤, 
add_conditional_edges로 priority == "긴급"이면 priority → notify → assign, 
그 외엔 priority → assign으로 분기하세요.

사용 파일: data/support_tickets.csv
기대 결과: 출력에 alert 열이 추가되고 긴급 티켓에만 "즉시알림"이 찍히면 성공.

[해답 보기] =======================================================
import sys, pathlib, csv
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import DATA
from langgraph.graph import StateGraph, START, END
from ch21_workflow import TicketState as Base, classify_node, priority_node, assign_node

class TicketState(Base):
    alert: str

def notify_node(state) -> dict:
    """긴급 티켓에 즉시 알림 플래그를 세팅한다."""
    return {"alert": "즉시알림"}

def route(state) -> str:
    """긴급이면 notify를 거치고, 아니면 바로 assign으로."""
    return "notify" if state["priority"] == "긴급" else "assign"

g = StateGraph(TicketState)
g.add_node("classify", classify_node)
g.add_node("priority", priority_node)
g.add_node("notify", notify_node)
g.add_node("assign", assign_node)
g.add_edge(START, "classify")
g.add_edge("classify", "priority")
g.add_conditional_edges("priority", route, {"notify": "notify", "assign": "assign"})
g.add_edge("notify", "assign")     # 알림 후 배정으로 합류
g.add_edge("assign", END)
workflow = g.compile()

with open(DATA / "support_tickets.csv", encoding="utf-8-sig") as f:
    tickets = list(csv.DictReader(f))

print(f"{'티켓':<7}{'우선순위':<7}{'알림':<8}{'담당팀'}")
for t in tickets:
    r = workflow.invoke({"content": t["content"]})
    print(f"{t['ticket_id']:<7}{r['priority']:<7}{r.get('alert','-'):<8}{r['team']}")
# ===========================================================
**예상 출력**
티켓     우선순위   알림      담당팀
TK001  긴급     즉시알림   결제지원팀
TK002  보통     -        일반상담팀
TK003  긴급     즉시알림   물류팀
TK005  높음     -        물류팀
===============================================================

**해설**: 긴급 티켓(TK001, TK003)만 `notify` 노드를 거쳐 "즉시알림"이 찍혔습니다. 
핵심은 `route` 함수가 우선순위를 보고 "notify" 또는 "assign"을 반환하고, 
`notify` 다음에 다시 `assign`으로 **합류**(`g.add_edge("notify", "assign")`)하는 것입니다. 
긴급은 "알림→배정", 일반은 "바로 배정"으로 흐르되, 결국 둘 다 배정을 거치죠. 
분기 후 합류하는 흐름 패턴입니다.


문제 2 — 노드 예외처리·검토필요 표시
각 노드를 try/except로 감싸 실패 시 state["error"]에 메시지를 기록하고, 
마지막 노드가 error가 있으면 team="검토필요"로 덮어쓰게 하세요.

검증: classify_node에 일부러 예외를 던지는 코드를 넣고, 
해당 티켓의 담당팀이 "검토필요"로 출력되는지 확인
기대 결과: 예외 발생 티켓이 "검토필요" 팀으로 처리되면 성공.

[해답 보기] =======================================================
import sys, pathlib, csv
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_chat, DATA
from typing import TypedDict
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from ch21_workflow import CATEGORIES, priority_node, TEAM_MAP

llm = get_chat(temperature=0)

class TicketState(TypedDict):
    content: str; category: str; priority: str; team: str; error: str

def classify_node(state) -> dict:
    try:
        # 검증용: 일부러 예외 던지기 (특정 내용에서)
        if "FORCE_ERROR" in state["content"]:
            raise ValueError("강제 예외 (테스트)")
        out = llm.invoke([SystemMessage(f"{CATEGORIES} 중 하나로 분류. 단어만."),
                          HumanMessage(state["content"])]).content.strip()
        cat = next((c for c in CATEGORIES if c in out), "기타")
        return {"category": cat, "error": ""}
    except Exception as e:
        return {"category": "기타", "error": f"분류 실패: {e}"}

def assign_node(state) -> dict:
    # error가 있으면 검토필요로 덮어씀
    if state.get("error"):
        return {"team": "검토필요"}
    return {"team": TEAM_MAP.get(state["category"], "일반상담팀")}

g = StateGraph(TicketState)
for name, fn in [("classify", classify_node), ("priority", priority_node), ("assign", assign_node)]:
    g.add_node(name, fn)
g.add_edge(START, "classify"); g.add_edge("classify", "priority")
g.add_edge("priority", "assign"); g.add_edge("assign", END)
workflow = g.compile()

tests = [{"ticket_id": "T1", "content": "결제가 안 돼요"},
         {"ticket_id": "T2", "content": "FORCE_ERROR 테스트 티켓"}]   # 예외 유발
for t in tests:
    r = workflow.invoke({"content": t["content"], "error": ""})
    print(f"{t['ticket_id']}: 팀={r['team']}, 오류={r.get('error') or '없음'}")
# =========================================================
**예상 출력**
T1: 팀=결제지원팀, 오류=없음
T2: 팀=검토필요, 오류=분류 실패: 강제 예외 (테스트)
===========================================================

**해설**: T2는 `FORCE_ERROR`로 예외가 났지만, 
**죽지 않고** `error`에 기록된 채 진행됐습니다. 
그리고 `assign_node`가 `error`가 있는 걸 보고 팀을 "검토필요"로 덮어썼죠. 
핵심은 두 가지 — (1) `try/except`로 예외를 잡아 죽지 않게, 
(2) 마지막 노드에서 `error`를 보고 후처리(검토필요 배정). 
이렇게 하면 실패한 티켓을 자동으로 "사람이 검토할 큐"로 보낼 수 있습니다. 
견고한 워크플로우의 핵심 패턴이죠.
