# FastAPI + MCP + ChromaDB + MySQL 멀티에이전트 프로젝트

## 1. 아키텍처

```text
웹/Swagger 사용자
      ↓
FastAPI (/api/chat)
      ↓
Supervisor Service
 ├─ 규칙/LLM/하이브리드 Router
 ├─ Sales Agent  → ChromaDB products 검색
 └─ Policy Agent → ChromaDB faq 검색
      ↓
MySQL consultations 기록

MCP Client ──STDIO──> MCP Server
                     ├─ ingest_knowledge
                     ├─ search_products
                     ├─ search_faq
                     └─ recent_consultations
```

## 2. 주요 기능

- OpenAI/Gemini 선택형 LLM
- 역할별 Sales/Policy 전문 에이전트
- Supervisor 규칙·LLM·하이브리드 라우팅
- ChromaDB PersistentClient 기반 Vector DB
- MySQL + SQLAlchemy 상담 이력 저장
- FastAPI REST API와 간단 웹 화면
- MCP Server 및 MCP Client 실습
- `app/core/common.py` 공통 모듈로 사용


## 3. MySQL 준비

Workbench에서 root 계정으로 `scripts/init_mysql.sql`을 실행합니다.

## 4. 설치

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
copy .env.example .env
```

`.env`에 실제 OpenAI 또는 Gemini API 키를 입력합니다.

## 5. FastAPI 실행

```bash
uvicorn app.main:app --reload --port 8000
```

- 웹 화면: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- 먼저 `POST /api/vector/ingest` 실행
- 이후 `POST /api/chat` 실행

요청 예시:

```json
{
  "question": "환불은 며칠 안에 신청해야 하나요?",
  "router_type": "hybrid",
  "provider": "gemini"
}
```

## 6. MCP 실행

서버 단독 실행:

```bash
python -m mcp_server.server
```

클라이언트 실행:

```bash
python -m mcp_client.client
```

MCP Server는 STDIO 프로토콜을 사용하므로 서버 코드에서 일반 `print()`를 사용하지 않습니다.

## 7. 테스트

```bash
pytest -q tests/test_router.py
```

`test_api.py`는 실제 MySQL이 실행 중이고 `.env` 연결정보가 맞을 때 실행합니다.
