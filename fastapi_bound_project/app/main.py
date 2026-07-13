"""FastAPI 애플리케이션 진입점입니다."""

from fastapi import FastAPI

from app.database import Base, engine
from app.routers import auth, boards

# 앱 실행 시 모델에 정의된 테이블을 자동으로 생성합니다(실습용).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FastAPI + MySQL 자유게시판 CRUD 백엔드",
    description="회원가입/로그인(JWT)과 자유게시글 CRUD를 제공하는 실습용 백엔드입니다.",
    version="1.0.0",
)

# 라우터를 등록합니다.
app.include_router(auth.router)
app.include_router(boards.router)


@app.get("/", tags=["root"], summary="헬스 체크")
def root():
    """서버가 정상 동작하는지 확인하는 기본 엔드포인트입니다."""
    return {"message": "FastAPI 자유게시판 백엔드가 실행 중입니다.", "docs": "/docs"}
