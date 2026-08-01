# OpenAI + Gemini LLM FastAPI App

이 프로젝트는 OpenAI API와 Gemini API를 모두 사용하여 다음 기능을 실행하는 FastAPI 기반 예제 앱입니다.

- 문장 생성
- 질의 응답
- 요약
- 번역
- 채팅
- 다양한 Use Case

## 1. 설치

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

## 2. 환경변수 설정

`.env.example` 파일을 `.env`로 복사한 뒤 API Key를 입력합니다.

```bash
copy .env.example .env
```

`.env` 예시:

```env
OPENAI_API_KEY=발급받은_OpenAI_API_KEY
GEMINI_API_KEY=발급받은_Gemini_API_KEY
OPENAI_MODEL=gpt-5.5
GEMINI_MODEL=gemini-2.5-flash
DEFAULT_TEMPERATURE=0.7
DEFAULT_TOP_P=0.95
DEFAULT_MAX_OUTPUT_TOKENS=800
DEFAULT_TIMEOUT_SECONDS=60
```

## 3. 실행

```bash
uvicorn app.main:app --reload
```

## 4. 접속

- UI 화면: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs
- Health Check: http://127.0.0.1:8000/api/health

## 5. API 예시

```bash
curl -X POST "http://127.0.0.1:8000/api/llm/openai/summary" ^
  -H "Content-Type: application/json" ^
  -d "{\"prompt\":\"LLM은 문장 생성, 요약, 번역, 질의응답에 활용된다.\",\"system_instruction\":\"핵심만 답변하시오.\",\"temperature\":0.3,\"top_p\":0.9,\"max_output_tokens\":500}"
```
