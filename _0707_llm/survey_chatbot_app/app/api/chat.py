# FastAPI 라우터를 만들기 위해 APIRouter를 불러옵니다.
from fastapi import APIRouter

# 요청과 응답 스키마를 불러옵니다.
from app.schemas.chat import ChatRequest, ChatResponse

# 챗봇 처리 서비스를 불러옵니다.
from app.services.chatbot_service import handle_chat

# /api/chat 관련 라우터 객체를 생성합니다.
router = APIRouter(prefix="/api", tags=["chat"])

# 사용자의 채팅 메시지를 처리하는 POST API입니다.
@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    # 서비스 계층에 메시지와 세션 ID를 전달해 응답을 생성합니다.
    result = handle_chat(request.message, request.session_id)

    # 딕셔너리 결과를 Pydantic 응답 모델로 변환합니다.
    return ChatResponse(**result)
