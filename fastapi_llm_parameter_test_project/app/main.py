# -*- coding: utf-8 -*-
"""FastAPI 앱 실행 시작 파일입니다."""

# 정적 파일 경로 계산을 위해 pathlib을 불러옵니다.
import pathlib

# FastAPI 애플리케이션 클래스를 불러옵니다.
from fastapi import FastAPI

# 루트 화면에서 HTML 파일을 반환하기 위해 FileResponse를 불러옵니다.
from fastapi.responses import FileResponse

# app/static 폴더를 웹에서 제공하기 위해 StaticFiles를 불러옵니다.
from fastapi.staticfiles import StaticFiles

# CORS 설정을 위해 미들웨어 클래스를 불러옵니다.
from fastapi.middleware.cors import CORSMiddleware

# LLM 테스트 라우터와 시스템 확인 라우터를 불러옵니다.
from app.routers import llm, system

# 현재 main.py 파일이 들어 있는 app 폴더 경로를 계산합니다.
APP_DIR = pathlib.Path(__file__).resolve().parent

# app/static 폴더 경로를 계산합니다.
STATIC_DIR = APP_DIR / "static"

# FastAPI 앱 객체를 생성합니다.
app = FastAPI(
    title="LLM API 실습 테스트 앱",
    description="HTML 강의 문서의 Gemini/OpenAI 호출 예제를 UI 화면에서 테스트하는 FastAPI 앱입니다.",
    version="2.0.0",
)

# 개발 중 프론트엔드 또는 외부 도구에서 접근할 수 있도록 CORS를 허용합니다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app/static 폴더를 /static URL로 제공하도록 등록합니다.
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 시스템 확인 API를 앱에 등록합니다.
app.include_router(system.router)

# LLM 실습 테스트 API를 앱에 등록합니다.
app.include_router(llm.router)


@app.get("/", include_in_schema=False)
def root():
    """브라우저에서 루트 경로로 접속하면 정적 UI 페이지를 반환합니다."""

    return FileResponse(STATIC_DIR / "index.html")
