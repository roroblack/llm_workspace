"""메인 화면, STT, GAN 생성 및 상태 조회 API를 정의합니다."""

# FastAPI 라우팅, 파일 업로드, 백그라운드 작업 기능을 가져옵니다.
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Request, UploadFile
# HTML 템플릿을 렌더링하기 위해 Jinja2Templates를 가져옵니다.
from fastapi.templating import Jinja2Templates
# 고유 작업 ID 생성을 위해 uuid4를 가져옵니다.
from uuid import uuid4
# 설정 객체를 가져옵니다.
from app.core.config import settings
# API 요청 및 응답 모델을 가져옵니다.
from app.schemas.generation import GenerationRequest, GenerationAcceptedResponse, TranscriptionResponse
# GAN 작업 함수를 가져옵니다.
from app.services.gan_service import run_generation_job
# 작업 상태 관리자를 가져옵니다.
from app.services.job_manager import job_manager
# 프롬프트 숫자 추출 함수를 가져옵니다.
from app.services.prompt_service import extract_target_digit
# 음성 저장 및 STT 함수를 가져옵니다.
from app.services.stt_service import get_stt_diagnostics, save_and_transcribe_audio

# API 엔드포인트를 묶는 라우터를 생성합니다.
router = APIRouter()
# 템플릿 디렉터리를 사용하는 렌더러를 생성합니다.
templates = Jinja2Templates(directory=str(settings.templates_dir))


# 애플리케이션 첫 화면을 반환합니다.
@router.get("/")
async def read_index(request: Request):
    """Google 검색창 형태의 메인 페이지를 반환합니다."""
    # index.html에 요청 객체와 애플리케이션 이름을 전달합니다.
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"app_name": settings.app_name},
    )


# 서버 상태 점검 API를 정의합니다.
@router.get("/api/health")
async def health_check() -> dict[str, str]:
    """서버 정상 실행 여부를 반환합니다."""
    # 정상 상태를 JSON으로 반환합니다.
    return {"status": "ok", "application": settings.app_name}


# STT 패키지, 장치 및 최근 오류 상태를 확인하는 진단 API를 정의합니다.
@router.get("/api/stt/diagnostics")
async def stt_diagnostics() -> dict:
    """STT 백엔드와 패키지 로딩 상태를 반환합니다."""
    # 서비스 모듈에서 수집한 진단 정보를 그대로 반환합니다.
    return get_stt_diagnostics()


# 녹음 음성을 저장하고 STT 변환하는 API를 정의합니다.
@router.post("/api/stt/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(audio: UploadFile = File(...)) -> TranscriptionResponse:
    """브라우저 음성을 저장하고 변환 텍스트를 반환합니다."""
    # 업로드 MIME 타입을 가져옵니다.
    content_type = audio.content_type or ""
    # 음성, 비디오 또는 일반 바이너리 업로드인지 확인합니다.
    if not (
        content_type.startswith("audio/")
        or content_type.startswith("video/")
        or content_type == "application/octet-stream"
    ):
        # 지원하지 않는 형식이면 400 오류를 반환합니다.
        raise HTTPException(status_code=400, detail=f"지원하지 않는 음성 형식입니다: {content_type}")
    # STT 입력 오류와 서버 오류를 구분하여 처리합니다.
    try:
        # 음성 저장과 텍스트 변환을 수행합니다.
        result = await save_and_transcribe_audio(audio)
        # 응답 모델로 변환하여 반환합니다.
        return TranscriptionResponse(**result)
    # 빈 음성이나 인식 실패 오류를 처리합니다.
    except ValueError as error:
        # 사용자 입력 문제를 400 오류로 반환합니다.
        raise HTTPException(status_code=400, detail=str(error)) from error
    # 모델 로딩이나 디코딩 오류를 처리합니다.
    except Exception as error:
        # 서버 내부 오류를 500 응답으로 반환합니다.
        raise HTTPException(
            status_code=500,
            detail=f"STT 처리 오류: {type(error).__name__}: {error}",
        ) from error


# GAN 이미지 생성 작업을 접수합니다.
@router.post("/api/generations", response_model=GenerationAcceptedResponse, status_code=202)
async def create_generation(
    request_data: GenerationRequest,
    background_tasks: BackgroundTasks,
) -> GenerationAcceptedResponse:
    """프롬프트 숫자 조건을 분석하고 GAN 작업을 백그라운드에 등록합니다."""
    # 프롬프트 입력 오류를 처리합니다.
    try:
        # 숫자 조건과 정규화 문장을 추출합니다.
        target_digit, normalized_prompt = extract_target_digit(request_data.prompt)
    # 숫자 조건을 찾지 못한 경우입니다.
    except ValueError as error:
        # 수정 가능한 입력 오류를 422로 반환합니다.
        raise HTTPException(status_code=422, detail=str(error)) from error
    # 고유 작업 ID를 생성합니다.
    job_id = uuid4().hex
    # 초기 작업 상태를 메모리에 저장합니다.
    job_manager.create(
        job_id,
        {
            "job_id": job_id,
            "status": "queued",
            "message": "GAN 작업이 대기열에 등록되었습니다.",
            "prompt": request_data.prompt,
            "normalized_prompt": normalized_prompt,
            "target_digit": target_digit,
            "epochs": request_data.epochs,
            "current_epoch": 0,
            "progress": 0,
            "epoch_images": [],
            "final_image_url": None,
        },
    )
    # HTTP 응답 후 실행할 GAN 작업을 등록합니다.
    background_tasks.add_task(
        run_generation_job,
        job_id,
        request_data.prompt,
        normalized_prompt,
        target_digit,
        request_data.epochs,
    )
    # 작업 ID와 분석 결과를 반환합니다.
    return GenerationAcceptedResponse(
        job_id=job_id,
        status="queued",
        target_digit=target_digit,
        normalized_prompt=normalized_prompt,
    )


# 특정 생성 작업 상태를 반환합니다.
@router.get("/api/generations/{job_id}")
async def get_generation(job_id: str) -> dict:
    """진행률, 손실값, 에포크 이미지 및 최종 결과를 반환합니다."""
    # 현재 작업 상태를 조회합니다.
    job = job_manager.get(job_id)
    # 존재하지 않는 작업인지 확인합니다.
    if job is None:
        # 잘못된 작업 ID이면 404를 반환합니다.
        raise HTTPException(status_code=404, detail="해당 생성 작업을 찾을 수 없습니다.")
    # 현재 작업 상태를 반환합니다.
    return job
