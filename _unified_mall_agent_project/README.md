# 승승장구몰 AI 커머스 에이전트 플랫폼 (통합 프로젝트)

llm_workspace의 28개 LLM/NLP 실습 프로젝트를 **하나의 실행 가능한 FastAPI 앱**으로 통합한 프로젝트.
가상 쇼핑몰 "승승장구몰"을 소재로, 커리큘럼(전처리→분류→LLM→에이전트)의 학습 성과를 결합한다.

> 학습 총정리는 [`교과목3_LLM_학습_공략집.md`](교과목3_LLM_학습_공략집.md) 참조.
> 작업 규칙은 [`RULE.md`](RULE.md), 계획/이력/리포트는 `plans/` `history/` `reports/` `debug_notes/` 참조.

## 구성 (Phase별 흡수)

| 영역 | 내용 | 흡수 레거시 |
|---|---|---|
| `app/core` | 설정(프로바이더 추상화 local/openai/gemini), 에러 taxonomy | 콘솔 common.py 다수 |
| `app/db` `app/auth` | SQLite+SQLAlchemy, JWT, 상품/주문/결제 CRUD | board_mysql, coffee |
| `app/tools` `app/agent` | 커머스 도구 6종, 수동 ReAct + LangChain 자동 에이전트 | react, agent_loop, function_calling, tool_system |
| `app/prompts` | 역할/few-shot/인젝션방어/CoT, CS 분류·오분류 루프, Planning | prompt/cot/planning 콘솔 |
| `app/rag` | 인덱싱/서비스 분리, FAISS, 로컬 임베딩, 요약 | vector_db, langchain_test |
| `app/ml` | 의도분류, KoELECTRA 감성분석, 임베딩 추천 | coffee/survey, Bert_sentiment, music |
| `app/lab` | 파라미터 실험, 토큰/비용, 유즈케이스 | llm_parameter, chatgpt, usage |
| `app/mcp` | MCP(Model Context Protocol) 서버/클라이언트 — 기존 도구·RAG·ML을 MCP 표준으로 노출(도구 10·리소스 2·프롬프트 1, stdio) | _0714_MCP(simple/rag/enterprise) |
| `app/static` | 챗 UI(멀티턴 화면 누적, 에이전트 단계 표시) | chatgpt/survey UI |

## 실행

```bash
pip install -r requirements.txt

# (선택) 빌드/오프라인 중 AI 파트를 로컬 Gemma로 대체 — 외부 토큰 0
python scripts/local_model_server.py     # http://127.0.0.1:8000/v1 (5GB, RAM 여유 필요)

# .env 설정 (최소 SECRET_KEY)
cp .env.example .env   # SECRET_KEY 등 채우기

# 앱 실행 (기동 시 DB 시딩 + RAG 인덱스 자동 빌드)
uvicorn app.main:app --reload
# → http://127.0.0.1:8000  (챗 UI), /docs (Swagger)
```

### 프로바이더 전환
- 빌드/오프라인: `.env`의 `LLM_PROVIDER=local` (로컬 Gemma, 토큰 0)
- 실서비스: `LLM_PROVIDER=openai` + `OPENAI_API_KEY`, 또는 `gemini` + `GOOGLE_API_KEY`
- **로컬 Gemma는 OpenAI tool-calling 미지원** → 요약·분류·프롬프트 등 평문 작업에 사용.
- **로컬에서 tool-calling까지 검증하려면 Qwen 사용**(토큰 0):
  ```bash
  LOCAL_GGUF_PATH="<Qwen3.5-4B-Q4_K_M.gguf>" CHAT_FORMAT="chatml-function-calling" \
  N_CTX=2048 N_BATCH=64 python scripts/local_model_server.py
  # 앱: LLM_PROVIDER=local, LOCAL_MODEL=qwen3.5-4b → 에이전트가 실제 도구 호출
  ```
  **에이전트 tool-calling이 로컬에서 실제 동작함을 검증 완료**(`/api/agent/chat` → `get_price` 도구 호출).
  근거: `debug_notes/2026-07-13_2130_*`, `reports/2026-07-13_2140_로컬_전체검증_리포트.md`. CPU라 느리고 RAM 3GB+ 필요.

| 모델 | 평문(요약·분류·RAG QA) | tool-calling(에이전트) |
|---|---|---|
| Gemma 4 E4B (로컬) | ✅ | ❌ |
| **Qwen3.5-4B (로컬)** | ✅ | **✅** |
| OpenAI / Gemini (실키) | ✅ | ✅ |
- 참고: 수동 ReAct(`/api/agent/chat`)는 OpenAI 호환(local/openai)만, Gemini는 LangChain 경로(`/api/agent/lc-chat`)에서 지원.

## 테스트

```bash
pytest -m "not llm and not ml"   # CI 기본(빠름, 모델 로드 없음)
pytest -m "not llm"              # 로컬 완료검증(실 임베딩/KoELECTRA 포함)
pytest -m "llm"                  # 로컬 Gemma/실키 서버 기동 시 라이브
```

## 주요 엔드포인트
- `POST /api/agent/chat` (수동 ReAct) / `/api/agent/lc-chat` (LangChain)
- `POST /auth/signup` `/auth/login`, `/api/products`, `/api/orders`, `/api/payments`
- `POST /api/rag/search` `/api/rag/summarize` `/api/rag/qa`(근거 기반 답변+출처 인용, TXT/PDF)
- `POST /api/nlp/intent` `/sentiment` `/recommend`
- `POST /api/lab/{basic,role,diversity,token-compare,estimate-cost,usecase}`
- `POST /api/mcp/tools` `/api/mcp/call` (앱이 MCP 클라이언트로 stdio 서버 호출 시연)
- `GET /api/health`

## 레거시 프로젝트
루트의 기존 28개 실습 폴더는 **학습 기록으로 보존**한다(삭제하지 않음). 각 기능이 본 통합
프로젝트의 어느 모듈로 흡수됐는지는 `reports/2026-07-12_1535_전체_프로젝트_반영_완전성_점검_리포트.md` 참조.
```
※ 원본 폴더 정리(보존/아카이브/삭제)는 사용자 결정 사항.
```

## 제약 / 참고
- 로컬 Gemma는 CPU 추론이라 느림. RAM 여유 부족 시 로드 실패(→ `debug_notes/` 참조).
- 토큰 카운트(lab)는 tiktoken cl100k 참고치로 로컬 Gemma 실제 토큰과 다름.
- 비용 추정은 `PRICE_TABLE` 등록 모델만(로컬은 과금 없음 → 대상 아님).
- MCP 서버는 `python -m app.mcp.server`(stdio)로도 단독 기동 가능(Claude Desktop 등 외부
  클라이언트 연결용). 단독 실행은 테이블 생성·seed를 하지 않으므로 DB(`data/mall.db`)가
  준비돼 있어야 한다(폴백 없음 — 미준비 시 오류 전파). 앱 경유(`/api/mcp/*`)는 학습용
  시연이라 요청마다 서버 subprocess를 띄운다(운영 구조 아님).
