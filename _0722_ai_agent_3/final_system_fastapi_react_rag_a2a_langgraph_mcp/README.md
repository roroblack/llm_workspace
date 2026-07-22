# Final System FastAPI Agent

기존 Python 콘솔 프로젝트를 FastAPI 앱 구조로 변환한 최종 프로젝트입니다.

웹 UI는 다음 네 기능 탭을 제공합니다.

- `RAG-TOOL-MEMORY 통합`: 기존 LangGraph 통합 채팅과 실행 추적
- `문의 처리 연계 부서 연결`: 교환·환불·반품 실행 요청을 MySQL `fastapi_db.customer_complaint`에 저장
- `요약 보고서 만들기`: 긴 원문을 map-reduce 방식으로 요약하고 마크다운 저장
- `임원용 매출 보고서 만들기`: `monthly_sales.csv` 확정 수치를 집계해 월간 보고서 저장

핵심 처리 구조:

```text
사용자 / 웹 UI / Swagger
        ↓
FastAPI REST API
        ↓
LangGraph 상태 그래프
        ├─ ReAct: 복합 질문의 도구 선택·실행·관찰
        ├─ RAG: 정책 PDF → 청크 → 임베딩 → FAISS 검색
        ├─ A2A: 주문·재고·FAQ·정책·교환 전문 에이전트 위임
        └─ MCP: 주문·재고·FAQ·교환 도구 표준 공개
        ↓
OpenAI 또는 Gemini
        ↓
data.zip 실데이터 / 정책 PDF
```

## 1. 프로젝트 구조

```text
final_system_fastapi_react_rag_a2a_langgraph_mcp/
├─ run.py
├─ requirements.txt
├─ .env.example
├─ README.md
├─ app/
│  ├─ main.py
│  ├─ api/
│  │  └─ routes.py
│  ├─ core/
│  │  ├─ common.py
│  │  ├─ settings.py
│  │  └─ logging_config.py
│  ├─ models/
│  │  └─ schemas.py
│  ├─ services/
│  │  ├─ data_service.py
│  │  ├─ llm_factory.py
│  │  └─ rag_service.py
│  ├─ agents/
│  │  ├─ tools.py
│  │  ├─ react_agent.py
│  │  └─ specialists.py
│  ├─ graph/
│  │  └─ workflow.py
│  ├─ mcp_server/
│  │  ├─ client.py
│  │  └─ server.py
│  ├─ templates/
│  │  └─ index.html
│  └─ static/
│     ├─ style.css
│     └─ app.js
├─ data/
│  ├─ orders.csv
│  ├─ inventory.csv
│  ├─ faq.csv
│  └─ docs/*.pdf
├─ tests/
├─ logs/
└─ cache/
```


## 2. 기술별 적용 내용

### ReAct

`app/agents/react_agent.py`에서 최신 LangChain `create_agent`를 사용합니다.

```text
질문 분석 → 도구 선택 → 도구 실행 → 결과 관찰 → 추가 도구 또는 최종 답변
```

사용 도구:

- `get_order_status`
- `get_stock`
- `search_faq`
- `policy_search`
- `request_exchange`

`InMemorySaver`와 `thread_id`를 사용해 멀티턴 대화를 기억합니다.

### RAG

`app/services/rag_service.py`에서 다음 순서로 정책 검색기를 만듭니다.

```text
data/docs/*.pdf
→ PyPDFLoader
→ RecursiveCharacterTextSplitter
→ OpenAI 또는 Gemini Embeddings
→ FAISS
→ similarity_search
```

정책 질문은 검색 근거를 먼저 수집한 뒤 근거 고정 프롬프트로 답변합니다.

### A2A

`app/agents/specialists.py`는 다음 역할별 에이전트를 제공합니다.

- `order-agent`
- `inventory-agent`
- `faq-agent`
- `policy-agent`
- `exchange-agent`

`GET /api/v1/a2a/agents`에서 에이전트 카드를 확인하고, `POST /api/v1/a2a/message`로 전문 에이전트에 직접 요청할 수 있습니다.

### LangGraph

`app/graph/workflow.py`는 `StateGraph`로 다음 흐름을 제어합니다.

```text
START
  ↓
classify
  ├─ rag → grounded_answer → END
  ├─ a2a → END
  ├─ mcp → END
  └─ react → END
```

`trace` 상태에는 각 단계의 실행 기록이 누적됩니다.

### MCP

`app/mcp_server/server.py`는 공식 MCP Python SDK의 `FastMCP`로 독립 실행 가능한 도구 서버를 제공합니다.

```bash
python -m app.mcp_server.server
```

제공 도구:

- `mcp_order_status`
- `mcp_stock`
- `mcp_faq`
- `mcp_request_exchange`

FastAPI 내부에서는 `app/mcp_server/client.py`의 동일 도구 레지스트리를 사용하므로 비즈니스 로직이 중복되지 않습니다.

## 3. PyCharm 실행 방법

### 3-1. 프로젝트 열기

PyCharm에서 압축 해제한 프로젝트 폴더를 엽니다.

### 3-2. 가상환경 생성

Python 3.11 또는 3.12 인터프리터를 권장합니다.

Windows 터미널:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 3-3. 환경변수 설정

`.env.example`을 복사해 `.env` 파일을 만듭니다.

```env
OPENAI_API_KEY=본인의_OpenAI_API_KEY
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBED_MODEL=text-embedding-3-small

GOOGLE_API_KEY=본인의_Google_API_KEY
GEMINI_MODEL=gemini-2.5-flash
GEMINI_EMBED_MODEL=models/gemini-embedding-001
```

OpenAI 또는 Gemini 중 하나만 사용할 경우 해당 공급자의 키만 설정해도 됩니다.

### 3-4. FastAPI 실행

PyCharm에서 `run.py`를 우클릭하고 실행합니다.

터미널 실행:

```bash
python run.py
```

접속 주소:

```text
웹 UI   : http://127.0.0.1:8000
Swagger : http://127.0.0.1:8000/docs
ReDoc   : http://127.0.0.1:8000/redoc
```

## 4. 주요 API

| 메서드 | URL | 설명 |
|---|---|---|
| GET | `/api/v1/health` | 서버와 API 키 설정 상태 |
| POST | `/api/v1/chat` | 전체 통합 워크플로우 실행 |
| POST | `/api/v1/complaints/connect` | 실행성 문의를 담당 부서 MySQL 큐에 저장 |
| POST | `/api/v1/reports/summary` | 요약 보고서 생성 |
| POST | `/api/v1/reports/sales` | 임원용 월간 매출 보고서 생성 |
| GET | `/api/v1/reports/{filename}` | 생성된 마크다운 보고서 다운로드 |
| POST | `/api/v1/tools/call` | 개별 MCP 호환 도구 실행 |
| GET | `/api/v1/a2a/agents` | A2A 에이전트 카드 목록 |
| POST | `/api/v1/a2a/message` | 전문 에이전트 직접 위임 |
| GET | `/api/v1/data/files` | data.zip 파일 목록 |
| POST | `/api/v1/rag/reset` | FAISS 메모리 캐시 초기화 |
| POST | `/api/v1/exercises/exchange` | 실습 1 교환 신청 도구 |
| GET | `/api/v1/exercises/memory` | 실습 2 메모리 격리 시나리오 |

## 5. 통합 채팅 요청 예

```json
{
  "message": "주문 O000050 상태 알려줘",
  "thread_id": "user-1001",
  "provider": "openai"
}
```

정책 RAG:

```json
{
  "message": "환불 절차와 조건을 정책 근거로 알려줘",
  "thread_id": "user-1001",
  "provider": "gemini"
}
```

멀티턴 메모리:

```text
1회: 환불 절차 알려줘
2회: 주문 O000050 상태 알려줘
3회: 아까 그 정책 다시 알려줘
```

세 요청의 `thread_id`를 동일하게 지정합니다.

## 6. 개별 도구 실행

```json
{
  "tool_name": "get_order_status",
  "arguments": {
    "order_id": "O000050"
  }
}
```

교환 접수 실습:

```json
{
  "tool_name": "request_exchange",
  "arguments": {
    "order_id": "O000050",
    "reason": "상품이 파손되어 도착함"
  }
}
```

## 7. A2A 직접 실행

```json
{
  "target_agent": "policy-agent",
  "message": "멤버십 등급별 혜택을 찾아줘",
  "provider": "openai",
  "thread_id": "a2a-user-1"
}
```

## 8. 테스트

API 키가 필요 없는 데이터 및 API 테스트:

```bash
pytest -q
```

실제 LLM과 RAG 통합 테스트는 `.env` 키와 인터넷 연결이 필요합니다.

### MySQL 준비

`.env.example`을 `.env`로 복사한 뒤 `MYSQL_USER`, `MYSQL_PASSWORD`를 로컬 환경에 맞게 설정합니다.
앱은 최초 실행성 문의에서 `fastapi_db`와 `customer_complaint` 테이블을 자동 준비합니다. DB 생성 권한이 없는 계정은 먼저 다음 스크립트를 실행합니다.

```bash
mysql -u root -p < mysql_init.sql
```

초기 저장 상태는 `receipt_status=0`, `resolution_status=0`이며 접수·처리 날짜는 `NULL`입니다.

## 9. 운영상 주의사항

- `InMemorySaver`는 서버를 재시작하면 대화가 초기화됩니다. 운영 환경에서는 Redis 또는 DB 체크포인터로 교체합니다.
- FAISS 인덱스는 공급자별로 메모리에 캐시됩니다.
- 기존 `request_exchange` 도구의 접수번호 생성은 교육용이며, 담당 부서 연계 저장은 별도 `customer_complaint` 흐름에서 실제 DB INSERT를 수행합니다.
- 쓰기 작업을 실제 서비스에 연결할 때는 사용자 인증, 권한, 명시적 확인, 감사 로그를 추가해야 합니다.
- `allow_origins=["*"]`는 개발 편의를 위한 값입니다. 배포 시 실제 프런트엔드 주소만 허용하십시오.
