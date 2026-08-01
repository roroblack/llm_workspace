"""
FastAPI 애플리케이션의 실행 진입점입니다.
"""

# FastAPI 클래스를 가져옵니다.
from fastapi import FastAPI

# 브라우저에서 JSON 대신 간단한 안내 HTML을 반환하기 위해 HTMLResponse를 가져옵니다.
from fastapi.responses import HTMLResponse

# 프로젝트 API Router를 가져옵니다.
from app.routers.api import router

# 설정 객체를 가져옵니다.
from app.config.settings import get_settings


# 캐시된 설정 객체를 가져옵니다.
settings = get_settings()

# FastAPI 애플리케이션 객체를 생성합니다.
app = FastAPI(
    title=settings.app_name,
    description="OpenAI GPT, MCP, FAISS/Qdrant, MySQL을 학습하는 RAG Assistant API",
    version="1.0.0",
)

# 프로젝트 REST API Router를 애플리케이션에 등록합니다.
app.include_router(router)


# 루트 URL에서 프로젝트 안내 화면을 반환합니다.
@app.get("/", response_class=HTMLResponse)
def home() -> str:
    """실행 확인과 주요 URL을 알려주는 간단한 HTML을 반환합니다."""

    # 브라우저에서 바로 확인할 수 있는 HTML 문자열을 반환합니다.
    return """
    <!doctype html>
    <html lang="ko">
    <head>
        <meta charset="utf-8">
        <title>MCP RAG Assistant</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; line-height: 1.7; }
            code { background: #f2f4f7; padding: 3px 7px; border-radius: 5px; }
            .box { border: 1px solid #d0d7de; border-radius: 10px; padding: 20px; }
        </style>
    </head>
    <body>
        <h1>FastAPI + OpenAI + MCP 기반 RAG Assistant</h1>
        <div class="box">
            <p>FastAPI 서버가 정상적으로 실행 중입니다.</p>
            <p>Swagger: <a href="/docs">/docs</a></p>
            <p>상태 확인: <a href="/api/health">/api/health</a></p>
            <p>먼저 Swagger에서 <code>POST /api/rag/rebuild</code>를 실행하세요.</p>
            <p>MCP 서버는 별도 터미널에서 <code>python -m mcp_server.server</code>로 실행합니다.</p>
        </div>
    </body>
    </html>
    """


# 이 파일을 직접 실행했을 때 Uvicorn 서버를 시작합니다.
if __name__ == "__main__":
    # ASGI 서버 실행 모듈을 가져옵니다.
    import uvicorn

    # 문자열 import 방식으로 FastAPI 앱을 실행합니다.
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
    )
