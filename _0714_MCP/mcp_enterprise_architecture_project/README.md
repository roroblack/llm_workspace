# MCP 실무 아키텍처 프로젝트

## 아키텍처

```text
사용자
  ↓
FastAPI
  ↓
OpenAI
  ↓
MCP Client
  ↓ stdio / JSON-RPC
MCP Server
  ├── File Tool
  ├── DB Tool
  ├── GitHub Tool
  ├── Slack Tool
  ├── Browser Tool
  ├── Calendar Tool
  ├── Email Tool
  ├── Vector Search Tool
  └── Python 실행 Tool
  ↓
외부 시스템
```

이 프로젝트는 PyCharm에서 각 계층의 역할을 직접 실행하고 확인할 수 있도록 구성했습니다.

## 프로젝트 구조

```text
mcp_enterprise_architecture_project/
├── app/                              # FastAPI 웹 애플리케이션
│   ├── main.py                       # 앱 생성, 라우터·정적 파일·템플릿 등록
│   ├── api/
│   │   ├── routes.py                 # 상태, Tool 호출, Assistant REST API
│   │   └── schemas.py                # API 요청 검증 모델
│   ├── core/
│   │   └── settings.py               # .env 기반 공용 설정과 데이터 경로
│   ├── services/
│   │   ├── assistant_service.py      # OpenAI Tool 선택과 MCP 실행 오케스트레이션
│   │   └── container.py              # 외부 시스템 어댑터 생성·공유
│   ├── templates/
│   │   └── index.html                # Tool을 확인·호출하는 웹 화면
│   └── static/
│       ├── app.js                    # 웹 UI와 REST API 연결
│       └── style.css                 # 웹 UI 스타일
├── mcp_client/
│   └── client.py                     # stdio로 MCP Server를 실행·호출하는 Client
├── mcp_server/
│   ├── server.py                     # FastMCP 서버, Tool·Resource·Prompt 등록
│   ├── tools/                        # 범주별 MCP Tool 정의
│   │   ├── file_tools.py
│   │   ├── db_tools.py
│   │   ├── github_tools.py
│   │   ├── slack_tools.py
│   │   ├── browser_tools.py
│   │   ├── calendar_tools.py
│   │   ├── email_tools.py
│   │   ├── vector_tools.py
│   │   └── python_tools.py
│   └── resources/
│       └── system_resources.py       # 실행 상태와 Tool 카탈로그 Resource
├── external_systems/                 # Tool이 위임하는 실제 작업 어댑터
│   ├── file_system.py                # 제한된 로컬 파일 읽기·쓰기
│   ├── database.py                   # SQLite 업무 메모
│   ├── github_api.py                 # GitHub Issue API·데모 모드
│   ├── slack_api.py                  # Slack API·데모 모드
│   ├── browser.py                    # 허용 호스트 기반 웹 문서 조회
│   ├── calendar_store.py             # 로컬 JSON 일정 저장소
│   ├── email_sender.py               # SMTP 이메일·데모 모드
│   ├── vector_store.py               # TF-IDF 인덱싱·검색
│   └── python_sandbox.py             # AST 기반 산술식 계산
├── data/
│   ├── files/                        # File Tool 허용 영역
│   ├── vector_docs/                  # Vector Search 원본 문서
│   └── calendar/events.json          # Calendar Tool 데이터
├── tests/
│   └── test_safe_tools.py            # 파일 경로·Python 계산 안전성 테스트
├── .env.example                      # 환경변수 예시
├── requirements.txt                  # Python 의존성
└── README.md
```

`__init__.py`는 트리에서 생략했습니다. `data/enterprise.db`와
`data/vector_index.json`은 각각 DB Tool과 Vector Search Tool을 처음 사용할 때 생성됩니다.

## 프로젝트 구조 분석

### 계층별 역할

| 계층 | 구성 | 역할 |
|---|---|---|
| 화면·API | `app/main.py`, `app/templates`, `app/static`, `app/api` | 사용자 입력을 받고 요청을 검증한 뒤 서비스 계층에 전달합니다. |
| 오케스트레이션 | `app/services/assistant_service.py` | MCP Tool 스키마를 OpenAI에 전달하고, 모델이 선택한 Tool을 실행한 뒤 최종 답변을 생성합니다. API 키가 없으면 로컬 Tool 안내 모드로 동작합니다. |
| MCP Client | `mcp_client/client.py` | 현재 Python 환경에서 MCP Server를 하위 프로세스로 실행하고 stdio/JSON-RPC 세션을 엽니다. |
| MCP Server | `mcp_server/server.py`, `mcp_server/tools`, `mcp_server/resources` | 16개 Tool과 2개 Resource, 1개 Prompt를 MCP 규격으로 공개합니다. Tool 함수는 실제 처리를 어댑터에 위임합니다. |
| 외부 시스템 | `external_systems` | 파일·DB·HTTP·SMTP·로컬 검색 등의 실제 작업과 입력 제한, 허용 목록, 데모 모드를 담당합니다. |
| 데이터·검증 | `data`, `tests` | 로컬 영속 데이터와 샘플 문서를 저장하고 핵심 안전 장치를 테스트합니다. |

### 요청 흐름

Tool을 직접 호출할 때는 OpenAI를 거치지 않습니다.

```text
웹 UI → POST /api/mcp/call → MCPClientService
      → stdio MCP Server → MCP Tool → 외부 시스템 어댑터 → 결과 반환
```

자연어 Assistant 요청은 OpenAI가 Tool을 선택하고 결과를 바탕으로 답변합니다.

```text
웹 UI → POST /api/assistant → AssistantService
      → MCP Tool 목록 조회 → OpenAI Tool 선택
      → MCP Client → MCP Server → 외부 시스템 어댑터
      → Tool 결과를 OpenAI에 전달 → 최종 답변 반환
```

### 설계 특징과 확장 시 고려사항

- MCP Tool 등록 코드와 외부 연동 코드를 분리해 새 시스템을 추가하거나 어댑터를 교체하기 쉽습니다.
- 안전 정책은 `external_systems`에 모여 있어 MCP 외의 경로에서 어댑터를 호출해도 동일한 검증을 적용할 수 있습니다.
- 현재 MCP Client는 Tool 목록 조회와 Tool 호출마다 새 서버 프로세스를 시작합니다. 학습·데모에는 단순하지만 요청량이 많아지면 지속 세션이나 프로세스 재사용을 고려할 수 있습니다.
- `AssistantService`는 OpenAI가 더 이상 Tool을 요청하지 않을 때까지 호출을 반복하며, `OPENAI_MAX_TOOL_ROUNDS`로 최대 실행 라운드를 제한합니다.
- 테스트는 Python 임의 실행 차단과 파일 경로 탈출 방지를 중심으로 구성되어 있습니다. API, MCP 연결, Calendar·Vector·DB, 데모/라이브 모드 테스트를 추가하면 회귀 방지 범위가 넓어집니다.

## Tool 구성

| 범주 | MCP Tool |
|---|---|
| File | `file_list`, `file_read`, `file_write` |
| DB | `db_add_note`, `db_list_notes`, `db_search_notes` |
| GitHub | `github_list_issues`, `github_create_issue` |
| Slack | `slack_post_message` |
| Browser | `browser_fetch_text` |
| Calendar | `calendar_create_event`, `calendar_list_events` |
| Email | `email_send` |
| Vector Search | `vector_rebuild_index`, `vector_search` |
| Python | `python_calculate` |

## 안전한 기본 동작

- `LIVE_MODE=false`에서는 GitHub, Slack, Email이 데모 결과를 반환합니다.
- File Tool은 `data/files` 폴더 밖에 접근할 수 없습니다.
- Browser Tool은 `.env`의 허용 호스트에만 접근합니다.
- DB Tool은 임의 SQL을 실행하지 않고 업무 메모 기능만 제공합니다.
- Python Tool은 임의 코드를 실행하지 않고 산술 표현식만 처리합니다.
- Calendar Tool은 로컬 JSON 파일을 사용합니다.
- Vector Search는 외부 모델 없이 TF-IDF 방식으로 작동합니다.

## 1. PyCharm에서 프로젝트 열기

압축을 해제한 뒤 `mcp_enterprise_architecture_project` 폴더를 엽니다.

Python 3.11 가상환경을 권장합니다.

## 2. 패키지 설치

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
Copy-Item .env.example .env
```

## 3. FastAPI 실행

```powershell
python -m app.main
```

접속 주소:

- 웹 UI: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- 상태: `http://127.0.0.1:8000/api/health`

## 4. MCP Server만 실행

```powershell
python -m mcp_server.server
```

stdio 서버는 화면을 제공하지 않고 MCP Client의 연결을 기다립니다.

## 5. MCP Inspector 실행

Node.js가 설치되어 있다면 다음 명령을 실행합니다.

```powershell
npx -y @modelcontextprotocol/inspector python -m mcp_server.server
```

## 6. 웹 UI에서 Tool 직접 호출

### Python 계산

Tool 이름:

```text
python_calculate
```

인수:

```json
{
  "expression": "(12 + 8) * 3"
}
```

### 파일 목록

```text
file_list
```

```json
{}
```

### 업무 메모 등록

```text
db_add_note
```

```json
{
  "title": "MCP 회의",
  "content": "금요일까지 Tool 연동을 완료한다."
}
```

### Vector 인덱스 생성

```text
vector_rebuild_index
```

```json
{}
```

### Vector 검색

```text
vector_search
```

```json
{
  "query": "MCP Tool 보안 원칙",
  "top_k": 2
}
```

### 일정 등록

```text
calendar_create_event
```

```json
{
  "title": "MCP 프로젝트 회의",
  "start": "2026-07-15T14:00:00",
  "end": "2026-07-15T15:00:00",
  "description": "Tool 통합 상태 점검"
}
```

## 7. OpenAI + MCP 자동 Tool 선택

`.env`에 API 키를 설정합니다.

```env
OPENAI_API_KEY=발급받은_OpenAI_API_KEY
OPENAI_MODEL=gpt-4.1-mini
OPENAI_MAX_TOOL_ROUNDS=5
```

FastAPI를 다시 시작한 뒤 웹 UI의 `OpenAI + MCP Assistant`에서 자연어로 요청합니다.

```text
업무 문서 목록을 확인해줘.
```

OpenAI Responses API는 MCP Server에서 받은 Tool 스키마를 보고 필요한 Tool을 선택합니다. FastAPI 내부의 MCP Client가 stdio로 MCP Server를 실행하고 Tool 결과를 OpenAI에 다시 전달합니다. 추가 작업이 필요하면 다음 Tool을 이어서 선택하며, 최종 응답에는 사용 모델과 Tool 실행 라운드·추적 정보가 포함됩니다.

## 8. 실제 GitHub, Slack, Email 연결

`.env`에서 다음 값을 설정합니다.

```env
LIVE_MODE=true

GITHUB_TOKEN=...
GITHUB_OWNER=...
GITHUB_REPO=...

SLACK_BOT_TOKEN=...
SLACK_CHANNEL_ID=...

SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
EMAIL_FROM=...
```

`LIVE_MODE=true`에서는 외부 시스템이 실제로 변경될 수 있으므로 테스트 저장소와 테스트 채널을 먼저 사용해야 합니다.

## 9. 테스트

```powershell
pytest -q
```

## 10. 주요 API

| Method | URL | 설명 |
|---|---|---|
| GET | `/api/health` | 서버 상태 |
| GET | `/api/mcp/tools` | MCP Tool 목록 |
| POST | `/api/mcp/call` | MCP Tool 직접 호출 |
| POST | `/api/assistant` | OpenAI + MCP Assistant |
