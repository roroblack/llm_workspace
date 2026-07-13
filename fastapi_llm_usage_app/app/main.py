# FastAPI 애플리케이션 생성을 위해 FastAPI 클래스를 가져옵니다.
from fastapi import FastAPI

# 정적 파일을 서비스하기 위해 StaticFiles 클래스를 가져옵니다.
from fastapi.staticfiles import StaticFiles

# HTML 파일 응답을 반환하기 위해 FileResponse 클래스를 가져옵니다.
from fastapi.responses import FileResponse

# LLM API 라우터를 가져옵니다.
from app.api.llm_router import router as llm_router

# FastAPI 앱 객체를 생성합니다.
app = FastAPI(
    # Swagger 문서에 표시될 앱 이름입니다.
    title="OpenAI + Gemini LLM FastAPI App",
    # Swagger 문서에 표시될 앱 설명입니다.
    description="문장 생성, 질의응답, 요약, 번역, 채팅, Use Case 예제를 OpenAI API와 Gemini API로 실행하는 앱입니다.",
    # 앱 버전입니다.
    version="1.0.0",
)

# /api/llm 경로의 LLM 라우터를 앱에 등록합니다.
app.include_router(llm_router)

# app/static 폴더를 /static URL로 서비스합니다.
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# 루트 URL에서 HTML UI를 반환합니다.
@app.get("/")
def index():
    # 사용자가 브라우저로 접속하면 index.html 파일을 반환합니다.
    return FileResponse("app/static/index.html")


# 서버 상태 확인용 엔드포인트입니다.
@app.get("/api/health")
def health():
    # 서버가 정상 실행 중임을 JSON으로 반환합니다.
    return {"status": "ok", "message": "LLM FastAPI server is running"}
