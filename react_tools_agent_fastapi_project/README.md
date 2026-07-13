# Tools 기반 ReAct Agent FastAPI 프로젝트

## 1. 프로젝트 개요

이 프로젝트는 `Tools를 활용한 ReAct 에이전트`를 PyCharm에서 바로 실행해 확인할 수 있도록 구성한 FastAPI 기반 실습 프로젝트입니다.

사용 기술:

- Python
- FastAPI
- Torch
- OpenAI API
- Gemini API
- LangChain Tools
- 로컬 Vector DB(JSON + Torch cosine similarity)

핵심 기능:

- OpenAI + LangChain Tools 기반 ReAct Agent
- 가격/재고/재주문 기준/주문상태 도구 호출
- Vector DB 검색 도구
- Torch 기반 재고 분석
- Gemini + Vector DB 보조 답변
- `max_steps`, 중복 호출 방지, history trimming 적용

---

## 2. 프로젝트 구조

```text
react_tools_agent_fastapi_project/
├─ app/
│  ├─ main.py
│  ├─ schemas.py
│  ├─ core/
│  │  └─ config.py
│  ├─ routers/
│  │  └─ api.py
│  ├─ services/
│  │  ├─ vector_db.py
│  │  ├─ tools_service.py
│  │  ├─ torch_service.py
│  │  ├─ react_agent.py
│  │  └─ gemini_service.py
│  └─ static/
│     ├─ index.html
│     ├─ style.css
│     └─ app.js
├─ data/
│  ├─ products.csv
│  ├─ inventory.csv
│  ├─ orders.csv
│  └─ docs/
├─ vector_store/
├─ common.py
├─ requirements.txt
├─ .env.example
├─ .gitignore
└─ README.md
```

---

## 3. PyCharm 실행 방법

### 1단계: 프로젝트 열기

PyCharm에서 `react_tools_agent_fastapi_project` 폴더를 엽니다.

### 2단계: 가상환경 생성

PyCharm Terminal에서 실행합니다.

```bash
python -m venv .venv
```

Windows PowerShell:

```bash
.venv\Scripts\activate
```

### 3단계: 패키지 설치

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4단계: 환경변수 설정

```bash
copy .env.example .env
```

`.env` 파일을 열어 API 키를 입력합니다.

```text
OPENAI_API_KEY=실제_OpenAI_API_Key
GOOGLE_API_KEY=실제_Gemini_API_Key
```

API 키가 없어도 다음 기능은 로컬로 확인할 수 있습니다.

- `/api/health`
- `/api/torch/stock-summary`
- `/api/tools/local-demo`
- `/api/vector/rebuild`
- `/api/vector/search`

### 5단계: 서버 실행

```bash
uvicorn app.main:app --reload
```

브라우저 접속:

```text
http://127.0.0.1:8000
```

Swagger 접속:

```text
http://127.0.0.1:8000/docs
```

---

## 4. 주요 API

| 메서드 | URL | 설명 |
|---|---|---|
| GET | `/` | 실습 UI 화면 |
| GET | `/api/health` | 서버/환경 상태 확인 |
| POST | `/api/vector/rebuild` | Vector DB 재생성 |
| POST | `/api/vector/search` | Vector DB 검색 |
| GET | `/api/torch/stock-summary` | Torch 재고 분석 |
| GET | `/api/tools/local-demo` | 로컬 도구 함수 확인 |
| POST | `/api/react/openai` | OpenAI + LangChain ReAct Agent |
| POST | `/api/gemini/ask` | Gemini + Vector DB 답변 |

---

## 5. ReAct 동작 흐름

```text
사용자 질문
↓
LLM이 필요한 도구 선택
↓
파이썬 코드가 도구 실행
↓
도구 결과를 Observation으로 저장
↓
LLM이 Observation을 보고 다음 행동 결정
↓
최종 답변 또는 다음 도구 호출
```

---

## 6. 예시 질문

```text
스마트워치 재고를 확인하고 재주문이 필요한지 알려줘.
```

```text
주문 O000106 배송 상태를 확인해줘.
```

```text
ReAct Agent Loop에서 무한루프를 막는 방법을 알려줘.
```

```text
이어버드 가격과 재고를 모두 확인해줘.
```

---

## 7. GitHub 업로드 명령

```bash
git init
git add .
git commit -m "Initial commit - ReAct tools agent FastAPI project"
git branch -M main
git remote add origin 본인_저장소_URL
git push -u origin main
```
