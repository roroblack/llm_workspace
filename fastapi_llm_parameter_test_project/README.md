# FastAPI LLM Parameter 실습 테스트 앱

브라우저 접속 주소:

```text
http://127.0.0.1:8000/
```

---

## 1. 주요 기능

- Gemini 기본 호출 테스트
- 시스템 지시로 역할과 말투 변경 테스트
- temperature 값에 따른 답변 다양성 측정
- 한국어/영어 토큰 사용량 비교
- OpenAI 호환 호출 구조 테스트
- `app/static/index.html` 기반 간단 UI 제공

---

## 2. 프로젝트 구조

```text
fastapi_llm_parameter_test_app/
├── app/
│   ├── main.py                  # FastAPI 앱 시작 파일, 정적 UI 연결
│   ├── common.py                # API Key와 Gemini 클라이언트 공통 관리
│   ├── schemas.py               # 요청/응답 데이터 구조
│   ├── routers/
│   │   ├── system.py            # health/env 확인 API
│   │   └── llm.py               # LLM 실습 테스트 API
│   ├── services/
│   │   └── llm_service.py       # Gemini/OpenAI 호출 로직
│   └── static/
│       ├── index.html           # 브라우저 UI 화면
│       ├── style.css            # UI 스타일
│       └── app.js               # API 호출 JavaScript
├── tests/
│   └── test_app.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 3. PyCharm에서 프로젝트 열기

1. PyCharm 실행
2. `File → Open`
3. `fastapi_llm_parameter_test_app` 폴더 선택
4. 하단 `Terminal` 열기

---

## 4. 가상환경 생성 및 패키지 설치

Windows PowerShell 또는 PyCharm 터미널에서 실행합니다.

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

macOS/Linux는 다음처럼 실행합니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

---

## 5. API Key 설정

`.env.example` 파일을 복사하여 `.env` 파일을 만듭니다.

Windows:

```bash
copy .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

`.env` 파일을 열고 값을 입력합니다.

```text
GOOGLE_API_KEY=실제_Gemini_API_KEY
GEMINI_MODEL=gemini-2.5-flash
OPENAI_API_KEY=선택_입력
```

OpenAI 실습은 선택입니다. `OPENAI_API_KEY`가 없어도 Gemini 테스트는 정상적으로 사용할 수 있습니다.

---

## 6. FastAPI 서버 실행

```bash
uvicorn app.main:app --reload
```

서버 실행 후 브라우저에서 접속합니다.

```text
http://127.0.0.1:8000/
```

---

## 7. UI 사용 순서

1. 브라우저에서 `http://127.0.0.1:8000/` 접속
2. 상단 `서버 상태 확인` 버튼 클릭
3. 원하는 테스트 카드에서 입력값 수정
4. 실행 버튼 클릭
5. 하단 `실행 결과` 영역에서 응답 확인

---

## 8. 내부 API 목록

UI는 아래 API를 JavaScript로 호출합니다.

| 메서드 | URL | 설명 |
|---|---|---|
| GET | `/` | UI 페이지 |
| GET | `/api/system/health` | 서버 상태 확인 |
| GET | `/api/system/env` | 환경변수 로드 상태 확인 |
| POST | `/api/llm/gemini/basic` | Gemini 기본 호출 |
| POST | `/api/llm/gemini/role` | 시스템 지시 역할 테스트 |
| POST | `/api/llm/gemini/diversity` | temperature 다양성 테스트 |
| POST | `/api/llm/gemini/token-compare` | 한국어/영어 토큰 비교 |
| POST | `/api/llm/openai/chat` | OpenAI 호출 테스트 |

Swagger도 유지되어 있으므로 필요하면 다음 주소에서 확인할 수 있습니다.

```text
http://127.0.0.1:8000/docs
```

테스트 순서:

/api/system/health 선택

Try it out 클릭

Execute 클릭

서버 상태가 ok로 나오는지 확인

----------
Gemini 테스트:

/api/llm/gemini/basic 선택

Try it out 클릭

요청 JSON 입력

```
{
  "message": "승승장구몰을 한 문장으로 홍보해줘.",
  "temperature": 0.7
}
```

Execute 클릭

응답 결과 확인

---

## 9. 자주 발생하는 오류

### GOOGLE_API_KEY 값이 없다는 오류

원인: `.env` 파일이 없거나 `GOOGLE_API_KEY`가 비어 있습니다.

해결:

```bash
copy .env.example .env
```

그 다음 `.env` 파일에 실제 Key를 입력합니다.

### ModuleNotFoundError

원인: 패키지 설치가 되지 않았거나 PyCharm 인터프리터가 다른 환경을 사용 중입니다.

해결:

```bash
pip install -r requirements.txt
```

PyCharm 오른쪽 아래 인터프리터가 현재 프로젝트의 `.venv`인지 확인합니다.
