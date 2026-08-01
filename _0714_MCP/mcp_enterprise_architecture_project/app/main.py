"""
FastAPI 애플리케이션 실행 진입점입니다.
"""

# FastAPI 애플리케이션 클래스를 가져옵니다.
from fastapi import FastAPI

# 정적 파일을 제공하기 위해 StaticFiles를 가져옵니다.
from fastapi.staticfiles import StaticFiles

# HTML 템플릿을 사용하기 위해 Jinja2Templates를 가져옵니다.
from fastapi.templating import Jinja2Templates

# 요청 객체 타입을 가져옵니다.
from fastapi import Request

# HTML 응답 타입을 가져옵니다.
from fastapi.responses import HTMLResponse

# API Router를 가져옵니다.
from app.api.routes import router

# 설정과 프로젝트 루트를 가져옵니다.
from app.core.settings import PROJECT_ROOT, get_settings


# 설정 객체를 가져옵니다.
settings = get_settings()

# FastAPI 애플리케이션 객체를 생성합니다.
app = FastAPI(
    title=settings.app_name,
    description="FastAPI → OpenAI → MCP Client → MCP Server → 외부 시스템 구조",
    version="1.0.0",
)

# REST API Router를 등록합니다.
app.include_router(router)

# 정적 파일 URL과 실제 폴더를 연결합니다.
app.mount(
    "/static",
    StaticFiles(directory=PROJECT_ROOT / "app" / "static"),
    name="static",
)

# Jinja2 템플릿 폴더를 설정합니다.
templates = Jinja2Templates(directory=PROJECT_ROOT / "app" / "templates")


# 루트 화면을 정의합니다.
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """MCP Tool을 확인하고 호출할 수 있는 웹 UI를 반환합니다."""

    # index.html 템플릿을 렌더링합니다.
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"app_name": settings.app_name},
    )


# 이 파일을 직접 실행하면 Uvicorn 서버를 시작합니다.
if __name__ == "__main__":
    # Uvicorn 모듈을 가져옵니다.
    import uvicorn

    # 개발 환경에서 자동 재시작을 활성화하여 실행합니다.
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
    )
