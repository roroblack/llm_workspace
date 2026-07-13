# -*- coding: utf-8 -*-
"""
FastAPI 애플리케이션 진입점입니다.

실행 명령:
    uvicorn app.main:app --reload

PyCharm에서는 app/main.py를 직접 실행하거나,
터미널에서 위 명령을 실행하면 됩니다.
"""

# pathlib.Path는 정적 파일 경로를 안전하게 지정하기 위해 사용합니다.
from pathlib import Path

# FastAPI는 웹 API 서버를 만들기 위한 프레임워크입니다.
from fastapi import FastAPI

# HTMLResponse는 index.html을 직접 반환할 때 사용합니다.
from fastapi.responses import HTMLResponse

# StaticFiles는 CSS/JS 같은 정적 파일을 서빙할 때 사용합니다.
from fastapi.staticfiles import StaticFiles

# API 라우터를 가져옵니다.
from app.routers.api import router as api_router

# 설정 객체를 가져옵니다.
from app.core.config import settings


# FastAPI 앱 객체를 생성합니다.
app = FastAPI(
    title=settings.app_name,
    description="Tools 기반 ReAct 에이전트를 FastAPI, Torch, OpenAI, LangChain, Vector DB로 구현한 PyCharm 프로젝트입니다.",
    version="1.0.0",
)

# 현재 파일 기준 static 폴더 경로를 계산합니다.
STATIC_DIR = Path(__file__).resolve().parent / "static"

# /static 경로로 정적 파일을 제공합니다.
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# /api 하위 경로에 API 라우터를 등록합니다.
app.include_router(api_router)


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    """브라우저에서 사용할 기본 실습 화면을 반환합니다."""
    # index.html 파일 경로를 지정합니다.
    html_path = STATIC_DIR / "index.html"

    # HTML 파일 내용을 읽어 응답합니다.
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


# 이 파일을 직접 실행할 때 uvicorn 서버를 띄웁니다.
if __name__ == "__main__":
    # uvicorn은 FastAPI 앱을 실행하는 ASGI 서버입니다.
    import uvicorn

    # 개발 모드로 서버를 실행합니다.
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
