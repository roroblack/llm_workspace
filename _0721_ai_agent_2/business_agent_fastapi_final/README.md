# Business Agent FastAPI Final

기존 `business_agent_console_project`의 월별 매출 집계, 안전한 예외 처리, 
OpenAI/Gemini 보고서 작성, 마크다운 저장, 카테고리 차트, 실습 기능을 
FastAPI 웹 앱으로 재구성한 프로젝트입니다.

## 아키텍처

```text
FastAPI UI / REST / Swagger
        ↓
LangGraph 분류 및 상태 제어
 ├─ ReAct: 복합 질문의 자율 도구 선택
 ├─ RAG: PDF·CSV 근거 검색
 ├─ A2A: 매출·보고서·지식·전략 전문 에이전트
 └─ MCP: 매출·CSV·파일 조회 표준 도구 서버
        ↓
OpenAI 또는 Gemini + data 폴더 + reports 폴더
```

## 실행

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
Copy-Item .env.example .env
python run.py
```

- 웹 UI: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## 독립 MCP 서버

```powershell
python -m app.mcp_server.server
```

## 주요 API

- `POST /api/v1/chat`: LangGraph 통합 실행
- `POST /api/v1/tools/call`: MCP 호환 도구 호출
- `GET /api/v1/a2a/agents`: 전문 에이전트 카드
- `POST /api/v1/a2a/message`: 전문 에이전트 직접 위임
- `GET /api/v1/data/files`: 원본 데이터 파일 목록
- `POST /api/v1/rag/reset`: FAISS 메모리 캐시 초기화
- `GET /api/v1/reports/{filename}`: 생성 보고서와 차트 다운로드

## 질문 예시

- `2026-05 월간 매출 보고서와 차트를 생성해 줘`
- `2026-04 매출과 전월 대비 성장률을 알려줘`
- `환불교환정책에 근거해 교환 조건을 설명해 줘`
- `최근 매출과 마케팅 브리프를 근거로 다음 달 전략을 제안해 줘`
- `mcp: 2026-03`
- `mcp: csv competitor_data.csv`

## 테스트

```powershell
pytest -q
```

API 키가 없어도 데이터 서비스와 MCP 호환 도구 테스트는 실행할 수 있습니다. 실제 ReAct, RAG 답변 생성에는 `.env`의 OpenAI 또는 Gemini API 키가 필요합니다.
