# FastAPI + MySQL 자유게시판 CRUD 백엔드

간단 회원가입, 간단 로그인, 자유게시글 등록/전체 조회/상세 조회/수정/삭제를 처리하는 FastAPI 백엔드 예제입니다.

## 1. 주요 기능

- 회원가입: `POST /auth/signup`
- 로그인: `POST /auth/login`
- 게시글 등록: `POST /boards`
- 게시글 전체 조회: `GET /boards`
- 게시글 상세 조회 + 조회수 1 증가: `GET /boards/{board_id}`
- 게시글 수정: `PUT /boards/{board_id}`
- 게시글 삭제: `DELETE /boards/{board_id}`
- Swagger 문서: `http://127.0.0.1:8000/docs`

## 2. 프로젝트 구조

```text
fastapi_board_mysql_project/
├─ app/
│  ├─ main.py
│  ├─ database.py
│  ├─ models.py
│  ├─ schemas.py
│  ├─ security.py
│  └─ routers/
│     ├─ auth.py
│     └─ boards.py
├─ .env.example
├─ .gitignore
├─ mysql_init.sql
├─ requirements.txt
└─ run_server.bat
```

## 3. MySQL 데이터베이스 생성

MySQL에 접속한 뒤 다음 SQL을 실행합니다.

```sql
CREATE DATABASE IF NOT EXISTS fastapi_board_db
DEFAULT CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

또는 프로젝트의 `mysql_init.sql` 파일을 실행합니다.

## 4. PyCharm 실행 순서

1. PyCharm 실행
2. `Open` 클릭
3. `fastapi_board_mysql_project` 폴더 선택
4. Python 3.11 인터프리터 선택 또는 `.venv` 생성
5. PyCharm Terminal에서 다음 명령 실행

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

6. `.env.example` 파일을 복사해 `.env` 파일 생성
7. `.env`의 MySQL 아이디, 비밀번호, DB명을 본인 환경에 맞게 수정
8. 서버 실행

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

또는 Windows에서 `run_server.bat` 실행

## 5. Swagger 테스트 순서

브라우저에서 다음 주소로 접속합니다.

```text
http://127.0.0.1:8000/docs
```

### 5-1. 회원가입

`POST /auth/signup` 실행

```json
{
  "username": "user01",
  "password": "1234",
  "name": "홍길동"
}
```

### 5-2. 로그인

`POST /auth/login` 실행

- username: `user01`
- password: `1234`

응답에서 `access_token`을 확인합니다.

### 5-3. Swagger Authorize 설정

1. Swagger 우측 상단 `Authorize` 클릭
2. username에 `user01` 입력
3. password에 `1234` 입력
4. `Authorize` 클릭
5. 닫기

이후 자물쇠가 걸린 게시글 등록/수정/삭제 API를 테스트할 수 있습니다.

### 5-4. 게시글 등록

`POST /boards` 실행

```json
{
  "title": "첫 번째 게시글",
  "content": "FastAPI와 MySQL을 연동한 게시글입니다."
}
```

### 5-5. 게시글 전체 조회

`GET /boards` 실행

### 5-6. 게시글 상세 조회

`GET /boards/{board_id}` 실행

상세 조회할 때마다 `view_count`가 1씩 증가합니다.

### 5-7. 게시글 수정

`PUT /boards/{board_id}` 실행

```json
{
  "title": "수정된 제목",
  "content": "수정된 내용입니다."
}
```

### 5-8. 게시글 삭제

`DELETE /boards/{board_id}` 실행

## 6. 주의 사항

- `.env` 파일은 비밀번호와 비밀키가 들어 있으므로 GitHub에 올리지 않습니다.
- 실습 프로젝트이므로 테이블은 앱 실행 시 자동 생성됩니다.
- 운영 프로젝트에서는 Alembic 마이그레이션, Refresh Token, 권한 관리, CORS 설정, 로깅, 예외 처리 구조화를 추가하는 것이 좋습니다.
