from pathlib import Path

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.recommender.music_recommender import MusicRecommender
from app.schemas.chat_schema import MusicChatRequest, MusicChatResponse, RecommendedSong
from app.services.openai_service import OpenAIChatService


# 현재 파일 기준으로 프로젝트의 app/data/music_dataset.json 경로를 계산합니다.
DATASET_PATH = Path(__file__).resolve().parents[1] / "data" / "music_dataset.json"

# FastAPI 라우터 객체를 생성합니다.
router = APIRouter(prefix="/api/chat", tags=["Music Chatbot"])

# PyTorch 추천 모델은 요청마다 새로 만들 필요가 없으므로 모듈 로딩 시 1회 생성합니다.
music_recommender = MusicRecommender(DATASET_PATH)


def get_openai_service(settings: Settings = Depends(get_settings)) -> OpenAIChatService:
    """
    OpenAIChatService 의존성 주입 함수입니다.

    FastAPI의 Depends 기능을 사용하면 라우터 함수에서 필요한 객체를
    깔끔하게 전달받을 수 있습니다.
    """
    return OpenAIChatService(settings)


@router.post("/music", response_model=MusicChatResponse)
def chat_music(
    request: MusicChatRequest,
    openai_service: OpenAIChatService = Depends(get_openai_service),
):
    """
    사용자 입력을 받아 PyTorch 추천 결과와 OpenAI 자연어 답변을 함께 반환합니다.
    """

    # PyTorch 추천 모델로 대표 감정과 추천 음악 목록을 구합니다.
    detected_mood, recommendations = music_recommender.recommend(
        user_message=request.message,
        top_k=request.top_k,
    )

    # Pydantic 모델에서 일반 dict 리스트로 변환하기 위해 대화 기록을 정리합니다.
    conversation_history = [message.model_dump() for message in request.conversation_history]

    # OpenAI ChatGPT API로 자연스러운 챗봇 답변을 생성합니다.
    answer = openai_service.generate_music_answer(
        user_message=request.message,
        detected_mood=detected_mood,
        recommendations=recommendations,
        conversation_history=conversation_history,
    )

    # 추천 음악 리스트를 응답 스키마에 맞게 변환합니다.
    response_recommendations = [
        RecommendedSong(
            title=song["title"],
            artist=song["artist"],
            mood=song["mood"],
            reason=song["reason"],
            url=song["url"],
            score=song["score"],
        )
        for song in recommendations
    ]

    # 최종 응답 객체를 반환합니다.
    return MusicChatResponse(
        answer=answer,
        detected_mood=detected_mood,
        recommendations=response_recommendations,
    )


@router.get("/songs")
def list_songs():
    """
    현재 앱에 등록된 음악 추천 데이터 전체를 반환합니다.
    """
    return {
        "count": len(music_recommender.songs),
        "songs": music_recommender.songs,
    }
