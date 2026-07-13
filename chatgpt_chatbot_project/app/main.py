# app/main.py
# ------------------------------------------------------------
# FastAPI 애플리케이션의 시작 파일입니다.
# 정적 HTML/CSS/JS 화면을 제공하고, /api/chat API로 챗봇 응답을 처리합니다.
# ------------------------------------------------------------

# pathlib의 Path는 운영체제에 안전한 경로 처리를 위해 사용합니다.
from pathlib import Path

# FastAPI는 웹 API 서버를 만드는 핵심 클래스입니다.
# HTTPException은 API 처리 중 오류 상태 코드를 반환할 때 사용합니다.
from fastapi import FastAPI, HTTPException

# StaticFiles는 HTML, CSS, JavaScript, 이미지 같은 정적 파일을 제공할 때 사용합니다.
from fastapi.staticfiles import StaticFiles

# FileResponse는 특정 파일을 HTTP 응답으로 반환할 때 사용합니다.
from fastapi.responses import FileResponse

# CORS 미들웨어는 프론트엔드와 백엔드 주소가 다를 때 브라우저 차단을 방지합니다.
from fastapi.middleware.cors import CORSMiddleware

# 요청과 응답 데이터 구조를 가져옵니다.
from app.schemas import ChatRequest, ChatResponse, ConfigResponse

# OpenAI API 호출을 담당하는 서비스 함수와 설정 관련 상수를 가져옵니다.
from app.services.openai_service import (
    generate_chat_reply,
    OPENAI_MODEL,
    AVAILABLE_MODELS,
    DEFAULT_SYSTEM_INSTRUCTION,
    client as openai_client,
)

# FastAPI 앱 객체를 생성합니다.
# title, description, version은 Swagger 문서 화면에 표시됩니다.
app = FastAPI(
    title="FastAPI ChatGPT ChatBot",
    description="제공된 React 챗봇 예제를 참고하여 FastAPI와 순수 HTML/JS로 다시 구현한 ChatGPT 챗봇 앱입니다.",
    version="1.0.0",
)

# CORS 허용 설정을 추가합니다.
# 개발 단계에서는 모든 출처를 허용하지만, 운영 배포에서는 실제 도메인만 허용하는 것이 안전합니다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 현재 파일 기준으로 app 디렉터리 경로를 계산합니다.
BASE_DIR = Path(__file__).resolve().parent

# 정적 파일이 들어 있는 static 디렉터리 경로를 계산합니다.
STATIC_DIR = BASE_DIR / "static"

# /static 주소로 CSS, JS, 이미지 파일을 제공하도록 설정합니다.
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# 브라우저에서 루트 주소로 접속했을 때 index.html을 반환합니다.
@app.get("/", response_class=FileResponse)
def read_index() -> FileResponse:
    # index.html 파일 경로를 생성합니다.
    index_file = STATIC_DIR / "index.html"

    # FileResponse를 사용하여 HTML 파일을 브라우저에 전달합니다.
    return FileResponse(index_file)


# 서버 상태 확인용 API입니다.
# 배포 후 서버가 정상 동작하는지 빠르게 확인할 때 사용합니다.
@app.get("/api/health")
def health_check() -> dict:
    # 간단한 JSON 응답을 반환합니다.
    return {"status": "ok", "message": "FastAPI ChatGPT chatbot server is running."}


# 프론트엔드 설정 화면을 초기화할 때 필요한 서버 정보를 반환하는 API입니다.
# 기본 모델명, 추천 모델 목록, 기본 System Instruction, API 키 설정 여부를 알려줍니다.
@app.get("/api/config", response_model=ConfigResponse)
def get_config() -> ConfigResponse:
    return ConfigResponse(
        default_model=OPENAI_MODEL,
        available_models=AVAILABLE_MODELS,
        default_system_instruction=DEFAULT_SYSTEM_INSTRUCTION,
        has_api_key=openai_client is not None,
    )


# 챗봇 질문을 처리하는 POST API입니다.
# 프론트엔드는 사용자가 입력한 메시지를 이 주소로 전송합니다.
@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    # try 블록 안에서 OpenAI API 호출 또는 데모 응답 생성을 처리합니다.
    try:
        # 서비스 함수에 사용자 질문, 이전 대화 기록, 설정값을 전달합니다.
        reply, used_demo_mode, used_model = generate_chat_reply(
            request.message,
            request.history,
            request.settings,
        )

        # 정해진 응답 형식으로 답변을 반환합니다.
        return ChatResponse(reply=reply, used_demo_mode=used_demo_mode, model=used_model)

    # 예상하지 못한 오류가 발생했을 때 500 상태 코드로 응답합니다.
    except Exception as exc:
        # 실제 운영 환경에서는 exc 내용을 그대로 노출하지 않는 것이 더 안전할 수 있습니다.
        raise HTTPException(status_code=500, detail=f"챗봇 응답 생성 중 오류가 발생했습니다: {exc}") from exc
