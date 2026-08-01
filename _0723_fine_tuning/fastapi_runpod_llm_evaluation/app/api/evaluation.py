"""
평가 실행과 Base/Fine-tuned 비교 API를 제공합니다.
"""

# FastAPI 라우터와 HTTP 오류 클래스를 가져옵니다.
from fastapi import APIRouter, HTTPException

# 평가 요청 데이터 스키마를 가져옵니다.
from app.models.schemas import (
    EvaluationCompareRequest,
    EvaluationRunRequest,
)

# 평가 서비스 객체를 가져옵니다.
from app.services.evaluation_service import evaluation_service


# /api/evaluation 경로 아래에서 사용할 라우터를 생성합니다.
router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


@router.post("/run")
def run_evaluation(request: EvaluationRunRequest) -> dict:
    """
    선택한 한 모델의 전체 평가를 동기적으로 실행합니다.
    """

    try:
        # 요청 값에 따라 모델 평가를 실행하고 결과를 반환합니다.
        return evaluation_service.run(
            model_kind=request.model_kind,
            use_bertscore=request.use_bertscore,
            limit=request.limit,
        )
    except (ValueError, RuntimeError, FileNotFoundError) as error:
        # 평가 설정이나 파일 오류를 400 응답으로 변환합니다.
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/compare")
def compare_models(request: EvaluationCompareRequest) -> dict:
    """
    동일한 평가 데이터로 Base와 Fine-tuned 모델을 순차 비교합니다.
    """

    try:
        # 두 모델 평가와 변화량 계산을 실행합니다.
        return evaluation_service.compare(
            use_bertscore=request.use_bertscore,
            limit=request.limit,
        )
    except (ValueError, RuntimeError, FileNotFoundError) as error:
        # 모델 또는 평가 데이터 오류를 400 응답으로 변환합니다.
        raise HTTPException(status_code=400, detail=str(error)) from error
