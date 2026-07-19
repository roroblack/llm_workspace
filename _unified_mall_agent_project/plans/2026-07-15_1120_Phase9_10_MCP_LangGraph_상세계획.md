# Phase 9·10 상세 계획 — MCP 서버/클라이언트 · LangGraph 워크플로

- 작성일시: 2026-07-15 11:20
- 상위: `plans/2026-07-12_1511_통합_계획서_v2.md` (Phase 5~8에 이은 확장)
- 흡수 출처:
  - `_0714_MCP/` — simple_mcp_server(FastMCP 기초), mcp_rag_project(MCP+RAG), mcp_enterprise_architecture(MCP 서버+클라이언트+external systems)
  - `_0715_LangGraph/agent_workflow_console_project` — StateGraph CS 티켓 워크플로
  - 강의: `from_colab_llm/0714-s/5_MCP이해_서버구축.pdf`
- 판정: **구현 가능** (mcp 1.28.1 = FastMCP 포함, langgraph 1.2.8 설치됨. 기존 통합 자산을 재사용하므로 자연스러운 확장)
- **진행 상태(2026-07-18)**: Phase 9(MCP) ✅ **완료·합의**(구현리포트 1617, Codex R1·R2 잔여결함 없음). Phase 10(LangGraph) ✅ **완료·합의**(구현리포트 1710, Codex 설계리뷰+구현 R1·R2 잔여결함 없음). **Phase 9·10 전부 완료.**

## 0. 구현 가능성 판단 (요약)
| 대상 | 가능? | 근거 |
|---|---|---|
| MCP 서버(도구/리소스/프롬프트 노출) | ✅ | `mcp.server.fastmcp.FastMCP` 설치됨. 통합의 커머스 도구·RAG QA를 그대로 노출 |
| MCP 클라이언트(서버 연결·호출) | ✅ | `mcp.client.stdio` 설치됨. FastAPI가 stdio로 MCP 서버 호출 |
| LangGraph StateGraph 워크플로 | ✅ | langgraph 설치됨. 통합의 분류/규칙 재사용해 명시적 그래프 구성 |
- 로컬 검증: MCP 도구 대부분(get_price 등)은 LLM 불필요 → 완전 검증. LLM 쓰는 노드(classify·rag_qa)는 로컬 Gemma/Qwen 평문으로 검증(에이전트 tool-calling과 달리 평문이라 OK).

---

## Phase 9 — MCP 서버 + 클라이언트

### 목표
통합 프로젝트의 기존 기능(커머스 도구·RAG QA·ML)을 **MCP 표준으로 노출**해, 외부 MCP 클라이언트(Claude Desktop 등)나 앱 내부에서 사용 가능하게 한다. "기능을 도구로 등록" → "표준 프로토콜로 노출"로 한 단계 확장.

### 설계 (기존 재사용, 중복 없음)
```
app/mcp/
├── __init__.py
├── server.py       # FastMCP 서버: 기존 commerce_tools·rag.qa·ml을 @mcp.tool로 노출
└── client.py       # stdio MCP 클라이언트 서비스(list_tools/call_tool)
app/routers/mcp.py  # POST /api/mcp/tools(목록), /api/mcp/call(호출) — 앱에서 MCP 서버 사용 시연
```
- **MCP 도구**(기존 함수 재사용, 얇은 래핑):
  - 커머스: get_price/get_stock/get_order_status/search_product/get_exchange_rate (→ `app.tools.commerce_tools`, db 세션은 서버가 생성)
  - RAG: `rag_qa`(→ `app.rag.qa.answer`), `vector_search`(→ `app.rag.service.search`)
  - ML: `analyze_sentiment`, `classify_intent`, `recommend_products`
- **MCP 리소스**: `config://runtime`(비밀 제외 설정), `catalog://products`(상품 목록)
- **MCP 프롬프트**: `grounded_rag_prompt`(검색 먼저·근거만 사용)
- **transport**: stdio(`python -m app.mcp.server`). Windows UTF-8 재설정 포함.
- **DB 세션**: MCP 서버는 별도 프로세스라 자체 SessionLocal 사용. 도구 실행마다 세션 open/close.

### 원칙(RULE)
- 기존 도구/서비스 **재사용**(중복 구현 금지). 얇은 @mcp.tool 래퍼만.
- 키/설정 없으면 ConfigError, 폴백 없음(기존과 동일).
- external_systems(browser/email/slack/github/python_sandbox 등)는 **미이관** — 실제 외부연동·샌드박스는 승승장구몰 범위 밖 + 보안 위험(YAGNI). 학습은 레거시 보존.

### 테스트
- 결정론: FastMCP 인스턴스에 도구/리소스/프롬프트가 등록됐는지, 도구 함수가 기존과 동일 결과(mock/실DB)
- 라이브(스모크): `mcp.client.stdio`로 서버 기동→`list_tools`(개수/이름)→`call_tool("get_price",{...})` 결과. LLM 도구는 로컬 모델로 1건.

### DoD
1. `app/mcp/server.py`가 커머스5+RAG2+ML3 도구, 리소스2, 프롬프트1 노출
2. MCP 클라이언트가 list_tools/call_tool 동작
3. `/api/mcp/*` 엔드포인트
4. 기존 회귀 없음
5. 로컬 스모크(get_price + rag_qa 1건)
6. 공략집·README·문서 갱신

---

## Phase 10 — LangGraph 워크플로

### 목표
통합의 분류/규칙을 **명시적 StateGraph**로 오케스트레이션. `create_agent`(암묵 ReAct)와 다른 **상태·노드·조건분기** 패턴을 학습·구현. CS 문의 처리 워크플로.

### 설계 (기존 분류 재사용)
```
app/workflow/
├── __init__.py
├── ticket_graph.py   # TicketState(TypedDict) + StateGraph: classify→priority→route(조건)→assign|escalate
└── rules.py          # calculate_priority/team/route (순수 규칙, LLM 무관)
app/routers/workflow.py  # POST /api/workflow/ticket → 최종 상태(category/priority/team/route/action)
```
- **State**: content, category, priority, team, route, action, error
- **노드**:
  - classify(LLM): `app.prompts.classifier` 재사용(문의 분류). chat 주입 가능(테스트/로컬)
  - priority/assign(규칙): rules.py
  - 조건분기: priority가 '긴급'이면 escalate, 아니면 assign (add_conditional_edges)
- ~~**linear** + **conditional** 두 그래프 제공(강의 대응)~~ → **[2026-07-18 설계변경, Codex 합의]**
  **conditional 그래프만 구현.** linear 그래프(classify→priority→assign, 분기 없음)는 (1) 엔드포인트
  미사용이고 (2) 미분류 입력에도 계속 진행해 합의 #3의 무폴백(미분류→manual_review→END)과 정면
  충돌하므로 YAGNI·RULE 위반. 강의 시연 목적만으로 잘못된 경로를 만들지 않는다.
  (Codex 설계 리뷰: `reports/_codex_phase10_design_review.txt`)
- **규칙 상수**(rules.py): 긴급={"불만","환불"}(도메인 정책, 명명 상수), 팀 매핑 7개 전부 명시,
  기본팀 없음(누락 시 ValidationErr 명시 실패). **State에서 error 필드 제거**(미분류는 정상 수동검토
  상태 category="미분류"+action="manual_review"로 표현, 실제 예외는 전파).

### 원칙(RULE)
- 분류는 기존 classifier 재사용. classify 노드 오류는 **삼키지 말고** error 필드+명시 처리(레거시의 '기타 폴백'은 RULE 위반이므로 → 분류 실패 시 error 기록 후 '미분류' sentinel, 폴백성 '기타' 금지)
- 규칙 함수는 순수(LLM 무관)

### 테스트
- 결정론: mock classify로 linear 그래프 상태 누적(classify→priority→assign), conditional 그래프 긴급→escalate/일반→assign 분기, rules 단위
- 라이브: 로컬 모델로 문의 1건 분류→워크플로 실행

### DoD
1. StateGraph(linear+conditional) 동작, 조건분기 검증
2. `/api/workflow/ticket` 엔드포인트
3. 분류 재사용, 폴백 없는 오류 처리
4. 기존 회귀 없음
5. 로컬 스모크 1건
6. 문서 갱신

---

## 공통 (기존 학습내용 보존)
- 기존 app 모듈·엔드포인트·테스트 **불변**. MCP/workflow는 **추가만**.
- 재사용: MCP=commerce_tools/rag.qa/ml, workflow=classifier/rules.
- 의존성: `mcp[cli]>=1.2,<2`, langgraph(이미 있음) → requirements 추가.
- 문서: 각 Phase마다 계획→Codex→구현→리포트→Codex점검, 공략집(스테이지 신설: MCP·LangGraph), README, 진행표, history, debug_notes.

## 미이관 (사유 기록)
- enterprise의 external_systems(실제 slack/github/email/browser/python_sandbox): 보안·범위 밖(YAGNI). 개념은 레거시 보존.
- MySQL knowledge_items: 통합은 SQLite 커머스 도메인이라 불필요.

## ★ Codex 합의 반영 (조건부 GO → 확정)
1. **MCP DB 세션**: `with_db(op, **kw)` 래퍼(요청별 open/finally close). **MCP 서버 단독 실행은 테이블 생성·seed 안 함**(FastAPI lifespan 없음) — DB 미준비 시 SQLAlchemy 예외 그대로 MCP 오류로 전파. `get_exchange_rate`는 세션 안 만듦. `catalog://products` 리소스도 자체 세션 open/close. "요청별 subprocess=학습용, 운영구조 아님" 명시.
2. **도구 10개 고정**: 커머스 5(get_price/get_stock/get_order_status/search_product/get_exchange_rate) + RAG 2(**vector_search**=service.search, **rag_qa**=qa.answer) + ML 3(sentiment/intent/recommend). **`search_knowledge_base`는 vector_search와 중복이라 MCP 노출 제외**(RULE 중복금지).
3. **LangGraph 분류 실패 처리(폴백 금지)**:
   - LLM 연결/API 실패 → 전파(요청 실패). 빈 입력 → ValidationErr.
   - LLM 출력이 허용 카테고리 아님 → `미분류` 기록 후 **`manual_review` 노드 → END**(priority로 계속 진행 금지 = 또 다른 폴백).
   - 유효 분류만 priority로. 그래프: `START→classify→(유효→priority→긴급/일반 | 미분류→manual_review→END)`.
4. **Phase 9·10 별도 세션**(각각 계획정합→구현→테스트→리포트→Codex→문서). 순서: 9(MCP)→10(LangGraph).
5. **테스트 마커**: MCP 등록/도구 결정론=기본, stdio subprocess=`@pytest.mark.mcp`, LLM=`@llm`, 모델=`@ml`. pyproject에 `mcp` 마커 추가, **CI=`not llm and not ml and not mcp`**.
6. **버전**: `mcp[cli]==1.28.1` 핀(검증값). langgraph==1.2.8은 **이미 requirements에 있음 → 재추가 안 함**.

## Codex 논의 포인트
1. MCP 서버를 별도 프로세스로 두고 도구는 기존 함수 재사용하는 설계가 정합한가(DB 세션 처리)
2. LangGraph classify 오류를 '기타 폴백' 대신 error+미분류로 하는 게 RULE에 맞나
3. Phase 9/10을 별개로 vs 함께
4. MCP 라이브 테스트(stdio 서브프로세스)의 CI 처리(@llm/@mcp 마커?)
5. external_systems 미이관이 타당한가
