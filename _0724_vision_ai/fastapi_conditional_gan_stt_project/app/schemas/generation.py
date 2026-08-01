"""이미지 생성 및 STT API의 데이터 모델을 정의합니다."""

# 요청값 검증을 위해 BaseModel과 Field를 가져옵니다.
from pydantic import BaseModel, Field


# GAN 생성 요청 구조를 정의합니다.
class GenerationRequest(BaseModel):
    """프롬프트와 학습 에포크 수를 전달받습니다."""
    # 사용자가 입력하거나 STT로 변환한 프롬프트입니다.
    prompt: str = Field(..., min_length=1, max_length=500)
    # 실행할 GAN 학습 에포크 수입니다.
    epochs: int = Field(default=5, ge=1, le=50)


# 생성 작업 접수 응답 구조를 정의합니다.
class GenerationAcceptedResponse(BaseModel):
    """생성 작업 식별자와 분석된 숫자 조건을 반환합니다."""
    # 상태 조회에 사용할 작업 ID입니다.
    job_id: str
    # 접수 직후 작업 상태입니다.
    status: str
    # 프롬프트에서 추출한 목표 숫자입니다.
    target_digit: int
    # 실제 모델 조건을 설명하는 정규화 프롬프트입니다.
    normalized_prompt: str


# STT 응답 구조를 정의합니다.
class TranscriptionResponse(BaseModel):
    """녹음 파일과 변환 텍스트 정보를 반환합니다."""
    # 녹음 작업의 고유 ID입니다.
    recording_id: str
    # 저장된 음성 파일 URL입니다.
    audio_url: str
    # 저장된 텍스트 파일 URL입니다.
    transcript_url: str
    # 음성에서 변환된 전체 문장입니다.
    text: str
    # 실제 변환에 사용된 STT 백엔드 이름입니다.
    backend: str
