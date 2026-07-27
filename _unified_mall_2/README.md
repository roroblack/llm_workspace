# 바로봄 AI 커머스·지식 상담 플랫폼 (프로덕션 최적화판)

기존 검증 자산(`_unified_mall_agent_project`, 결정론 182 테스트)을 **실제 사용 가능한 수준으로 최적화**하는
프로덕션 지향 프로젝트다. 학습용 통합본을 기준선으로 삼아, 개념적 Clean Architecture와 수직 Strangler로
포트화·주문 승인 루프·역할/관리자·요구사항↔테스트 매트릭스를 단계적으로 도입한다.

> 📐 시스템 아키텍처 설계 보고서(다이어그램 포함): [`docs/architecture.md`](docs/architecture.md)
> 규범 계획서: [`docs/plans/2026-07-19_1400_v3.1_통합구현계획서.md`](docs/plans/2026-07-19_1400_v3.1_통합구현계획서.md) (Codex 고도화·승인)
> 작업 규칙: [`RULE.md`](RULE.md) (무하드코딩·무폴백·YAGNI·검증우선·리포트의무·phased) — 원본에서 승계
> 원본 v3.0 계획: `AI_에이전트_커머스_지식바운티_통합_구현계획서_LLM용.md`

## 현재 상태 (Phase 0 기준선)

`_unified_mall_agent_project`의 검증된 제품을 **무변경 전체 복제**한 기준선이다. 결정론 **182 테스트 통과**
(CI 154 + MCP 8 + ML 20)를 동일 재현했다. 아직 **최적화(Phase 1~7) 전** 상태다.

**현재 실제로 있는 것** (허위 주장 금지 — RULE 1.1):
- FastAPI 앱, SQLite + SQLAlchemy, JWT **로그인**(username/password) — 단, **역할(role) 없음**
- 상품/재고/주문/결제 CRUD + E2E — 단, **장바구니(Cart) 없음**, 주문 승인 경계 없음(POST 즉시 재고차감)
- 커머스 도구(get_price/stock/order/search/exchange), 수동 ReAct + LangChain 에이전트(이중)
- RAG(FAISS + ko-sroberta, TXT/PDF, 답변 단위 출처 인용), 프롬프트/분류
- ML(KoELECTRA 감성·규칙 의도·임베딩 추천), MCP stdio 서버·클라이언트(읽기 도구 10), LangGraph 티켓 워크플로
- **관리자 화면/역할 없음**, 음성/화상/WebAuthn/바운티 경제 **없음**

**최적화로 추가될 것**(v3.1 MUST): 답변 단위 출처+abstention 품질 고정, 주문 미리보기→명시 승인→멱등,
단일 에이전트 닫힌 루프, MCP=REST 유스케이스 통일, USER/ADMIN·최소 관리자, 모델 레지스트리, 요구사항 매트릭스.
음성/화상/Passkey/풀 바운티/4모델 라우터/pgvector는 **후속**(범위 밖).

## 실행

```bash
pip install -r requirements.txt
# (Phase 2 이후) 명시적 migration + ingest 명령으로 DB·인덱스 준비
uvicorn app.main:app --reload
```

## 테스트

```bash
pytest -m "not llm and not ml and not mcp"   # CI 기본(154)
pytest -m "mcp"                              # MCP stdio(8)
pytest -m "not llm"                          # + 실 모델 로드(ML 포함)
```

## 거버넌스 폴더

| 폴더 | 용도 |
|---|---|
| `docs/plans/` | 단계별 계획서(v3.1 + Phase별) |
| `docs/history/` | 시간순 작업 이력(추가만) |
| `docs/reports/` | 작업 리포트(검증 로그 포함, 매 세션 필수) |
| `legacy/` | 대체·폐기 코드 보존 |
| `docs/` | 자산·데이터 매니페스트, 아키텍처 |
