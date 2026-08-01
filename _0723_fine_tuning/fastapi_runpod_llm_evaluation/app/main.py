"""
FastAPI 애플리케이션의 메인 진입점입니다.
"""

# 파일 경로 처리를 위해 Path를 가져옵니다.
from pathlib import Path

# FastAPI 애플리케이션과 Request 객체를 가져옵니다.
from fastapi import FastAPI, Request

# 정적 파일 제공 기능을 가져옵니다.
from fastapi.staticfiles import StaticFiles

# Jinja2 HTML 템플릿 기능을 가져옵니다.
from fastapi.templating import Jinja2Templates

# 각 기능별 API 라우터를 가져옵니다.
from app.api import evaluation, inference, system

# 애플리케이션 설정을 가져옵니다.
from app.core.config import get_settings


# 현재 app 디렉터리의 절대 경로를 계산합니다.
APP_DIR = Path(__file__).resolve().parent

# 환경변수 기반 설정 객체를 읽습니다.
settings = get_settings()

# FastAPI 애플리케이션 객체를 생성합니다.
app = FastAPI(
    title=settings.app_name,
    description=(
        "RunPod GPU와 연계하여 기반 모델과 파인튜닝 모델의 "
        "한국어 답변 품질 및 추론 성능을 비교하는 API입니다."
    ),
    version="1.0.0",
)

# /static 경로로 CSS와 JavaScript 파일을 제공하도록 설정합니다.
app.mount(
    "/static",
    StaticFiles(directory=str(APP_DIR / "static")),
    name="static",
)

# HTML 템플릿이 위치한 디렉터리를 지정합니다.
templates = Jinja2Templates(
    directory=str(APP_DIR / "templates")
)

# 시스템 상태 API를 애플리케이션에 등록합니다.
app.include_router(system.router)

# 단일 질문 추론 API를 등록합니다.
app.include_router(inference.router)

# 모델 평가 및 비교 API를 등록합니다.
app.include_router(evaluation.router)


@app.get("/")
def index(request: Request):
    """
    브라우저에서 사용할 평가 실습 화면을 반환합니다.
    """

    # index.html에 요청 객체와 애플리케이션 이름을 전달합니다.
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"app_name": settings.app_name},
    )
