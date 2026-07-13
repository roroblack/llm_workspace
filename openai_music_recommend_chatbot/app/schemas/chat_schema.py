from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """
    이전 대화 기록 하나를 표현하는 스키마입니다.

    role은 user 또는 assistant 값을 사용합니다.
    content에는 실제 대화 문장을 저장합니다.
    """

    role: str = Field(..., description="대화 발화자 역할: user 또는 assistant")
    content: str = Field(..., description="대화 내용")


class MusicChatRequest(BaseModel):
    """
    음악 추천 챗봇에 사용자가 보내는 요청 스키마입니다.
    """

    message: str = Field(..., description="사용자 입력 문장")
    conversation_history: list[ChatMessage] = Field(
        default_factory=list,
        description="브라우저에서 보관한 이전 대화 기록",
    )
    top_k: int = Field(
        default=3,
        ge=1,
        le=5,
        description="추천받을 음악 개수",
    )


class RecommendedSong(BaseModel):
    """
    추천 결과로 반환할 음악 한 곡의 정보입니다.
    """

    title: str = Field(..., description="음악 제목")
    artist: str = Field(..., description="가수 또는 연주자")
    mood: str = Field(..., description="대표 감정")
    reason: str = Field(..., description="추천 이유")
    url: str = Field(..., description="음악 또는 영상 URL")
    score: float = Field(..., description="PyTorch 유사도 점수")


class MusicChatResponse(BaseModel):
    """
    음악 추천 챗봇 응답 스키마입니다.
    """

    answer: str = Field(..., description="OpenAI ChatGPT가 생성한 자연어 답변")
    detected_mood: str = Field(..., description="추천 모델이 추정한 대표 감정")
    recommendations: list[RecommendedSong] = Field(..., description="추천 음악 목록")
