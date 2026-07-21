# -*- coding: utf-8 -*-
"""Business Agent FastAPI 애플리케이션의 시작 모듈입니다."""

# 애플리케이션 시작과 종료 처리를 위해 asynccontextmanager를 가져옵니다.
from contextlib import asynccontextmanager
# FastAPI 핵심 클래스를 가져옵니다.
from fastapi import FastAPI, Request
# 정적 파일을 서비스하기 위해 StaticFiles를 가져옵니다.
from fastapi.staticfiles import StaticFiles
# HTML 템플릿 렌더링을 위해 Jinja2Templates를 가져옵니다.
from fastapi.templating import Jinja2Templates
# API 라우터를 가져옵니다.
from app.api.routes import router
# 앱 이름과 경로 설정을 가져옵니다.
from app.core.settings import APP_NAME, APP_VERSION, ROOT


@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작과 종료 시 필요한 초기화 지점을 제공합니다."""
    # 시작 시점에는 경로 설정 모듈이 필요한 폴더를 이미 생성하므로 그대로 진행합니다.
    yield
    # 종료 시점에 별도 외부 자원이 없어 추가 정리는 수행하지 않습니다.

# 제목, 버전, 문서 주소, lifespan을 적용한 FastAPI 객체를 생성합니다.
app = FastAPI(title=APP_NAME, version=APP_VERSION, description="ReAct → RAG → A2A → LangGraph → MCP 통합 Business Agent", lifespan=lifespan)
# static 폴더를 /static URL에 연결합니다.
app.mount("/static", StaticFiles(directory=str(ROOT / "app" / "static")), name="static")
# HTML 템플릿 폴더를 설정합니다.
templates = Jinja2Templates(directory=str(ROOT / "app" / "templates"))
# /api/v1 REST API 라우터를 애플리케이션에 등록합니다.
app.include_router(router)


@app.get("/")
def index(request: Request):
    """Swagger 없이도 사용할 수 있는 웹 UI를 반환합니다."""

    # 최신 Starlette 방식:
    # 첫 번째 인자에 request 객체,
    # 두 번째 인자에 HTML 템플릿 파일명,
    # 세 번째 인자에 템플릿에서 사용할 데이터를 전달합니다.
    return templates.TemplateResponse(
        request,
        "index.html",
        {"app_name": APP_NAME},
    )