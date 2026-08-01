# app/main.py
# FastAPI 앱의 시작점입니다.

from fastapi import FastAPI  # FastAPI 애플리케이션 객체를 만들기 위해 사용합니다.
from app.database import Base, engine  # 테이블 생성에 필요한 Base와 DB 엔진입니다.
import app.models  # noqa: F401  # 테이블 자동 생성 전에 모든 ORM 모델을 Base에 등록하기 위해 임포트합니다.
from app.routers import auth, boards, menus, orders, payments  # 인증/게시판/메뉴/주문/결제 라우터를 가져옵니다.

# 개발/실습 편의를 위해 앱 시작 시 ORM 모델 기준으로 테이블을 자동 생성합니다.
# 운영 환경에서는 Alembic 같은 마이그레이션 도구 사용을 권장합니다.
Base.metadata.create_all(bind=engine)  # users, boards, menus, orders, order_items, payments 테이블을 자동 생성합니다.

app = FastAPI(  # FastAPI 앱 객체를 생성합니다.
    title="FastAPI MySQL 주문/결제 CRUD API",  # Swagger 문서 상단 제목입니다.
    description="간단 회원가입/로그인과 함께 회원·메뉴·주문내역·결제 정보를 DB에 저장/관리하는 백엔드 예제입니다.",  # Swagger 설명입니다.
    version="2.0.0",  # API 버전입니다.
)

app.include_router(auth.router)  # /auth 경로의 회원 인증 API를 앱에 등록합니다.
app.include_router(menus.router)  # /menus 경로의 메뉴 CRUD API를 앱에 등록합니다.
app.include_router(orders.router)  # /orders 경로의 주문 API를 앱에 등록합니다.
app.include_router(payments.router)  # /payments 경로의 결제 API를 앱에 등록합니다.
app.include_router(boards.router)  # /boards 경로의 게시판 API를 앱에 등록합니다.(기존 기능 유지)


@app.get("/")
def root():
    # 서버 실행 확인용 기본 API입니다.
    return {"message": "FastAPI MySQL 주문/결제 API가 실행 중입니다. /docs에서 Swagger를 확인하세요."}  # 상태 메시지를 반환합니다.
