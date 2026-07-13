# FastAPI ChatGPT 챗봇 앱 프로젝트

제공된 React 챗봇 예제를 참고하여 FastAPI 백엔드와 순수 HTML/CSS/JavaScript 화면으로 다시 작성한 ChatGPT 챗봇 프로젝트입니다.

## 1. 프로젝트 특징

- FastAPI로 백엔드 API 구현
- `/api/chat` 엔드포인트로 ChatGPT 응답 처리
- API 키를 프론트엔드 코드에 직접 넣지 않도록 `.env` 사용
- HTML/CSS/JavaScript 기반 floating chatbot UI 구현
- API 키가 없을 때도 화면 테스트가 가능한 데모 모드 제공
- 설정 메뉴에서 System Instruction, model, temperature, top_p, top_k, max_output_tokens 조정 가능
- 이전 대화 기록을 포함한 문맥 유지
- gpt-5 / o 계열 모델의 temperature 미지원 오류 자동 회피
- Swagger 문서 자동 제공

## 2. 프로젝트 구조

```text
fastapi_chatgpt_chatbot_project/
├─ app/
│  ├─ main.py                         # FastAPI 실행 파일
│  ├─ schemas.py                      # 요청/응답 데이터 모델
│  ├─ services/
│  │  └─ openai_service.py            # OpenAI API 호출 서비스
│  └─ static/
│     ├─ index.html                   # 챗봇 메인 화면
│     ├─ style.css                    # 챗봇 UI 스타일
│     └─ app.js                       # 챗봇 프론트엔드 동작
├─ .env.example                       # 환경 변수 예시
├─ .gitignore                         # Git 제외 파일 목록
├─ requirements.txt                   # 설치 패키지 목록
├─ run.bat                            # Windows 실행 스크립트
└─ README.md                          # 프로젝트 설명서
```

## 3. 실행 방법

### 3-1. 프로젝트 폴더로 이동

```bash
cd fastapi_chatgpt_chatbot_project
```

### 3-2. 가상환경 생성

```bash
python -m venv .venv
```

### 3-3. 가상환경 활성화

Windows CMD:

```bash
.venv\Scripts\activate
```

PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

### 3-4. 패키지 설치

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 3-5. 환경 변수 파일 생성

`.env.example` 파일을 복사하여 `.env` 파일을 만듭니다.

```bash
copy .env.example .env
```

`.env` 파일을 열고 OpenAI API 키를 입력합니다.

```env
OPENAI_API_KEY=sk-본인의_API_키
OPENAI_MODEL=gpt-4o-mini
```

API 키를 입력하지 않으면 데모 모드로 실행됩니다.

### 3-6. 서버 실행

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

또는 Windows에서 다음 파일을 실행합니다.

```bash
run.bat
```

## 4. 접속 주소

챗봇 화면:

```text
http://127.0.0.1:8000
```

Swagger API 문서:

```text
http://127.0.0.1:8000/docs
```

서버 상태 확인:

```text
http://127.0.0.1:8000/api/health
```

## 5. Swagger 테스트 방법

1. 브라우저에서 `http://127.0.0.1:8000/docs` 접속
2. `POST /api/chat` 클릭
3. `Try it out` 클릭
4. Request body에 아래 예시 입력

```json
{
  "message": "FastAPI가 무엇인지 설명해줘",
  "history": []
}
```

5. `Execute` 클릭
6. `reply` 값으로 챗봇 답변 확인

## 6. 중요한 보안 수정 사항

제공된 기존 React 코드에는 OpenAI API 키가 프론트엔드 JavaScript 안에 직접 작성되어 있었습니다. 프론트엔드 코드는 브라우저에서 누구나 확인할 수 있으므로 API 키를 넣으면 안 됩니다.

이 프로젝트에서는 API 키를 `.env` 파일에 저장하고, FastAPI 서버에서만 읽도록 수정했습니다. `.env` 파일은 `.gitignore`에 포함되어 GitHub에 올라가지 않도록 설정했습니다.

## 7. GitHub 업로드 명령

```bash
git init
git add .
git commit -m "Initial FastAPI ChatGPT chatbot project"
git branch -M main
git remote add origin 본인_깃허브_저장소_URL
git push -u origin main
```
