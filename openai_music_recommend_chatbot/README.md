# OpenAI ChatGPT API + FastAPI + PyTorch 음악 추천 챗봇

이 프로젝트는 **감성 단어 기반 음악 추천 챗봇** 아이디어를 FastAPI 앱으로 구현한 예제입니다.

핵심 흐름은 다음과 같습니다.

1. 감성 단어를 기준으로 음악 추천 데이터를 수집합니다.
2. 사용자의 감정 또는 상황을 입력받습니다.
3. 감정과 연결된 음악 URL을 추천합니다.
4. 챗봇 시나리오를 만들어 사용자가 자연스럽게 음악을 추천받도록 구성합니다.

본 프로젝트에서는 위 내용을 다음 기술로 구현했습니다.

- FastAPI: 백엔드 API 서버
- OpenAI ChatGPT API: 자연어 대화 응답 생성
- PyTorch: 감성 문장과 음악 데이터 간 유사도 계산
- HTML/CSS/JavaScript: 브라우저 채팅 UI
- JSON 데이터셋: 감성 키워드별 추천 음악 데이터

---

## 1. 프로젝트 구조

```text
openai_music_recommend_chatbot_fastapi_pytorch/
│
├── app/
│   ├── main.py
│   ├── api/
│   │   └── chat_router.py
│   ├── core/
│   │   └── config.py
│   ├── schemas/
│   │   └── chat_schema.py
│   ├── services/
│   │   └── openai_service.py
│   ├── recommender/
│   │   └── music_recommender.py
│   ├── data/
│   │   └── music_dataset.json
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── style.css
│       └── app.js
│
├── scripts/
│   └── google_video_url_collector.py
│
├── .env.example
├── requirements.txt
└── README.md
```

---

## 2. 실행 방법

### 2-1. 가상환경 생성

```bash
python -m venv .venv
```

### 2-2. 가상환경 활성화

Windows PowerShell:

```powershell
.venv\Scripts\activate
```

### 2-3. 패키지 설치

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 2-4. 환경변수 파일 생성

Windows CMD:

```cmd
copy .env.example .env
```

PowerShell:

```powershell
Copy-Item .env.example .env
```

`.env` 파일을 열고 OpenAI API Key를 입력합니다.

```env
OPENAI_API_KEY=sk-proj-본인키
OPENAI_MODEL=gpt-5.5
```

### 2-5. 서버 실행

```bash
uvicorn app.main:app --reload
```

### 2-6. 접속 주소

```text
브라우저 UI: http://127.0.0.1:8000
Swagger 문서: http://127.0.0.1:8000/docs
```

---

## 3. 주요 API

### 채팅 + 음악 추천

```http
POST /api/chat/music
```

요청 예시:

```json
{
  "message": "오늘 너무 우울해서 조용한 노래를 듣고 싶어요.",
  "conversation_history": [],
  "top_k": 3
}
```

### 추천 데이터 전체 조회

```http
GET /api/chat/songs
```

---

## 4. PyTorch 추천 방식

이 프로젝트는 복잡한 대규모 학습 모델 대신 수업용으로 이해하기 쉬운 
**키워드 벡터 기반 추천 모델**을 사용합니다.

1. 전체 감성 키워드 사전을 만듭니다.
2. 사용자 문장을 PyTorch Tensor 벡터로 변환합니다.
3. 음악 데이터의 감성 태그도 Tensor 벡터로 변환합니다.
4. Cosine Similarity로 가장 유사한 음악을 추천합니다.

---

## 5. 주의사항

- 실제 서비스에서는 YouTube URL, 음악 정보, 이미지 사용 시 저작권 표기가 필요합니다.
- 제공된 기본 데이터는 교육용 샘플입니다.
- `scripts/google_video_url_collector.py`는 
- Selenium 기반 URL 수집 코드를 최신 Selenium 방식으로 정리한 선택 실행용 스크립트입니다.
