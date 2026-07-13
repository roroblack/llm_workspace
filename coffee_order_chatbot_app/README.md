# Coffee Order AI Chatbot

FastAPI + OpenAI + PyTorch 기반 커피 주문 챗봇 예제입니다.

## 주요 기능

- PyTorch 간단 의도 분류 모델
- OpenAI ChatGPT 자연어 응답 생성
- 커피 메뉴 추천
- 장바구니 담기
- 데모 결제 진행 안내
- HTML/CSS/JavaScript 기반 웹 UI

## 백엔드 실습 기능 (DB 저장 · 인증)

SQLAlchemy ORM 기반으로 회원 · 메뉴 · 주문 · 결제 정보를 DB(기본 SQLite: `data/coffee.db`)에 저장합니다.

- 간단 회원가입/로그인 + JWT 토큰 발급 (`/auth/signup`, `/auth/login`), 비밀번호는 bcrypt 해싱 저장
- 메뉴 CRUD API (`/menus`) — 앱 최초 실행 시 기본 커피 메뉴 자동 시딩
- 주문 API (`/orders`) — 재고·금액 계산, 주문 시점 단가/이름 스냅샷 저장
- 결제 API (`/payments`) — 본인/중복/결제수단 검증 후 주문 상태 PAID로 갱신
- 계층 구조: `routers`(HTTP) → `services`(비즈니스 로직) → `models`(ORM)

Swagger 문서(`http://127.0.0.1:8000/docs`)에서 전체 API를 확인할 수 있습니다.

## 실행 방법

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

브라우저에서 접속합니다.

```text
http://127.0.0.1:8000
```

## OpenAI API 키 설정

`.env` 파일에 API 키를 입력합니다.

```text
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
```

API 키가 없으면 로컬 fallback 메시지로 동작합니다.
