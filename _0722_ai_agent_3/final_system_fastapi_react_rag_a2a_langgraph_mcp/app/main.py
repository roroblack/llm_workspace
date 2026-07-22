# -*- coding: utf-8 -*-
"""FastAPI 애플리케이션 진입점입니다."""

# asynccontextmanager는 FastAPI lifespan 시작 및 종료 처리를 정의합니다.
from contextlib import asynccontextmanager

# FastAPI는 API 서버 객체를 생성합니다.
from fastapi import FastAPI, Request
# CORSMiddleware는 브라우저의 교차 출처 요청을 제어합니다.
from fastapi.middleware.cors import CORSMiddleware
# HTMLResponse는 루트 웹 UI를 HTML로 반환합니다.
from fastapi.responses import HTMLResponse
# StaticFiles는 CSS와 JavaScript 같은 정적 파일을 제공합니다.
from fastapi.staticfiles import StaticFiles
# Jinja2Templates는 HTML 템플릿을 렌더링합니다.
from fastapi.templating import Jinja2Templates

# API 라우터를 가져옵니다.
from app.api.routes import router
# 로깅과 설정을 가져옵니다.
from app.core.logging_config import setup_logging
from app.core.settings import PROJECT_ROOT, get_settings

# 애플리케이션 환경설정 객체를 한 번 읽습니다.
settings = get_settings()
# 공용 구조적 로거를 초기화합니다.
logger = setup_logging()
# templates 폴더를 사용하는 Jinja2 렌더러를 생성합니다.
templates = Jinja2Templates(directory=str(PROJECT_ROOT / "app" / "templates"))


# lifespan 함수는 서버 시작과 종료 시 실행할 작업을 정의합니다.
@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 프로세스 생명주기 동안 초기화와 종료 로그를 기록합니다."""
    # 서버 시작 정보를 로그에 남깁니다.
    logger.info("FastAPI 시작: app=%s version=%s", settings.app_name, settings.app_version)
    # yield 전까지가 시작 단계이고 이후가 종료 단계입니다.
    yield
    # 서버가 정상 종료될 때 로그를 남깁니다.
    logger.info("FastAPI 종료")


# FastAPI 앱 객체를 생성하고 Swagger 메타데이터를 설정합니다.
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="ReAct → RAG → A2A → LangGraph → MCP 구조를 적용한 통합 CS 에이전트",
    lifespan=lifespan,
)
# 설정된 출처에서 브라우저 API 호출을 허용하도록 CORS 미들웨어를 등록합니다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# /static 경로에 정적 파일 폴더를 연결합니다.
app.mount("/static", StaticFiles(directory=str(PROJECT_ROOT / "app" / "static")), name="static")
# 모든 /api/v1 엔드포인트를 앱에 등록합니다.
app.include_router(router)


# root 함수는 Swagger 없이 사용할 수 있는 웹 채팅 화면을 제공합니다.
@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    """통합 에이전트 테스트 UI를 렌더링합니다."""
    # index.html 템플릿에 요청 객체와 앱 이름을 전달합니다.
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"app_name": settings.app_name, "version": settings.app_version},
    )
