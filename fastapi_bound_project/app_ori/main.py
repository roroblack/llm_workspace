# app/main.py
# FastAPI 앱의 시작점입니다.

from fastapi import FastAPI  # FastAPI 애플리케이션 객체를 만들기 위해 사용합니다.
from app.database import Base, engine  # 테이블 생성에 필요한 Base와 DB 엔진입니다.
from app.routers import auth, boards  # 회원 인증 라우터와 게시판 라우터를 가져옵니다.

# 개발/실습 편의를 위해 앱 시작 시 ORM 모델 기준으로 테이블을 자동 생성합니다.
# 운영 환경에서는 Alembic 같은 마이그레이션 도구 사용을 권장합니다.
Base.metadata.create_all(bind=engine)  # users, boards 테이블이 없으면 자동 생성합니다.

app = FastAPI(  # FastAPI 앱 객체를 생성합니다.
    title="FastAPI MySQL 자유게시판 CRUD API",  # Swagger 문서 상단 제목입니다.
    description="간단 회원가입, 로그인, 자유게시글 CRUD, 조회수 증가 기능을 제공하는 백엔드 예제입니다.",  # Swagger 설명입니다.
    version="1.0.0",  # API 버전입니다.
)

app.include_router(auth.router)  # /auth 경로의 회원 인증 API를 앱에 등록합니다.
app.include_router(boards.router)  # /boards 경로의 게시판 API를 앱에 등록합니다.


@app.get("/")
def root():
    # 서버 실행 확인용 기본 API입니다.
    return {"message": "FastAPI MySQL 자유게시판 API가 실행 중입니다. /docs에서 Swagger를 확인하세요."}  # 상태 메시지를 반환합니다.
