# Survey AI Chatbot

FastAPI + OpenAI + PyTorch 기반 설문조사 챗봇 앱입니다.

## 주요 기능

- FastAPI 백엔드 서버
- HTML/CSS/JavaScript 채팅 UI
- PyTorch 기반 간단 의도 분류
- OpenAI API 기반 자연어 응답 생성
- 설문 질문 진행, 답변 저장, 요약 출력
- 구글 설문지 링크 안내

## 프로젝트 구조

```text
survey_chatbot_app/
├─ app/
│  ├─ api/
│  │  └─ chat.py
│  ├─ core/
│  │  └─ config.py
│  ├─ data/
│  │  └─ survey_questions.json
│  ├─ models/
│  │  └─ intent_model.py
│  ├─ schemas/
│  │  └─ chat.py
│  ├─ services/
│  │  ├─ chatbot_service.py
│  │  ├─ openai_service.py
│  │  └─ survey_service.py
│  ├─ static/
│  │  ├─ app.js
│  │  └─ style.css
│  ├─ templates/
│  │  └─ index.html
│  └─ main.py
├─ .env.example
├─ requirements.txt
├─ run.py
└─ README.md
```

## 실행 방법

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
copy .env.example .env
python run.py
```

브라우저에서 아래 주소로 접속합니다.

```text
http://127.0.0.1:8000
```

## 환경변수 설정

`.env` 파일을 만들고 다음 값을 입력합니다.

```text
OPENAI_API_KEY=발급받은_API_KEY
OPENAI_MODEL=gpt-4o-mini
SURVEY_LINK=https://forms.gle/실제_구글_설문지_주소
```

## Swagger 테스트

```text
http://127.0.0.1:8000/docs
```

`POST /api/chat` 요청 예시입니다.

```json
{
  "message": "설문 시작",
  "session_id": "test-user-1"
}
```

## PDF 내용 반영 사항

강의안의 핵심 흐름인 채팅방 메뉴 구성, 응답 메시지 작성, 메시지 버튼 링크 연결, 구글 설문지 작성 흐름을 FastAPI 웹앱 방식으로 재구성했습니다.
