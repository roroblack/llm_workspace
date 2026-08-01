# FastAPI 앱을 만들기 위해 FastAPI를 불러옵니다.
from fastapi import FastAPI, Request

# 정적 파일 제공을 위해 StaticFiles를 불러옵니다.
from fastapi.staticfiles import StaticFiles

# HTML 템플릿 렌더링을 위해 Jinja2Templates를 불러옵니다.
from fastapi.templating import Jinja2Templates

# 앱 제목 설정을 가져옵니다.
from app.core.config import APP_TITLE

# 채팅 API 라우터를 가져옵니다.
from app.api.chat import router as chat_router

# FastAPI 앱 객체를 생성합니다.
app = FastAPI(title=APP_TITLE)

# static 폴더를 /static URL로 연결합니다.
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# templates 폴더를 Jinja2 템플릿 경로로 등록합니다.
templates = Jinja2Templates(directory="app/templates")

# 채팅 API 라우터를 앱에 등록합니다.
app.include_router(chat_router)

# 메인 화면을 렌더링하는 라우트입니다.
@app.get("/")
def index(request: Request):
    # index.html 템플릿에 request와 app_title 값을 전달합니다.
    return templates.TemplateResponse("index.html", {"request": request, "app_title": APP_TITLE})

# 서버 상태 확인용 API입니다.
@app.get("/api/health")
def health():
    # 서버가 정상 실행 중임을 알려주는 JSON을 반환합니다.
    return {"status": "ok", "message": "Survey AI Chatbot server is running"}
