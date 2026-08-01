from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.chat_router import router as chat_router
from app.core.config import get_settings


# .env 설정값을 읽어옵니다.
settings = get_settings()

# FastAPI 앱 객체를 생성합니다.
app = FastAPI(
    title=settings.APP_TITLE,
    description="OpenAI ChatGPT API와 PyTorch 추천 모델을 사용하는 음악 추천 챗봇",
    version="1.0.0",
)

# /static URL로 CSS, JavaScript 같은 정적 파일을 제공하도록 설정합니다.
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# HTML 템플릿 파일이 있는 폴더를 지정합니다.
templates = Jinja2Templates(directory="app/templates")

# 음악 추천 챗봇 API 라우터를 앱에 등록합니다.
app.include_router(chat_router)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """
    브라우저에서 접속했을 때 채팅 UI 페이지를 반환합니다.
    """
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "app_title": settings.APP_TITLE,
        },
    )


@app.get("/api/health")
def health_check():
    """
    서버가 정상 실행 중인지 확인하는 헬스 체크 API입니다.
    """
    return {
        "status": "ok",
        "message": "Music recommendation chatbot server is running.",
    }
