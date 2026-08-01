"""
단일 질문에 대한 모델 추론 API를 제공합니다.
"""

# FastAPI 라우터와 HTTP 오류 클래스를 가져옵니다.
from fastapi import APIRouter, HTTPException

# 요청과 응답 데이터 스키마를 가져옵니다.
from app.models.schemas import GenerationRequest, GenerationResponse

# 실제 추론 서비스 객체를 가져옵니다.
from app.services.inference_service import inference_service


# /api/inference 경로 아래에서 사용할 라우터를 생성합니다.
router = APIRouter(prefix="/api/inference", tags=["inference"])


@router.post("/generate", response_model=GenerationResponse)
def generate(request: GenerationRequest) -> GenerationResponse:
    """
    선택한 모델로 질문에 대한 답변을 생성합니다.
    """

    try:
        # 추론 서비스에 요청을 전달하고 결과를 반환합니다.
        return inference_service.generate(request)
    except (ValueError, RuntimeError, FileNotFoundError) as error:
        # 사용자 설정 또는 모델 로딩 오류를 400 응답으로 변환합니다.
        raise HTTPException(status_code=400, detail=str(error)) from error
