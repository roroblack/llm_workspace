# Pydantic 모델을 정의하기 위해 BaseModel과 Field를 불러옵니다.
from pydantic import BaseModel, Field

# 사용자가 채팅 API로 보내는 요청 형식입니다.
class ChatRequest(BaseModel):
    # 사용자가 입력한 메시지입니다.
    message: str = Field(..., min_length=1, description="사용자 입력 메시지")

    # 사용자를 구분하기 위한 세션 ID입니다.
    session_id: str = Field(default="default", description="대화 세션 ID")

# 챗봇이 채팅 API에서 반환하는 응답 형식입니다.
class ChatResponse(BaseModel):
    # 챗봇 답변 텍스트입니다.
    reply: str

    # PyTorch 모델이 예측한 사용자 의도입니다.
    intent: str

    # 의도 예측 신뢰도입니다.
    confidence: float

    # 현재 설문 진행 단계입니다.
    step: int

    # 전체 설문 문항 수입니다.
    total_steps: int
