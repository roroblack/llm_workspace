"""Image Captioning, Stable Diffusion, STT, TTS를 제공하는 FastAPI 진입점입니다."""

# 업로드 파일을 안전하게 저장하기 위한 UUID를 가져옵니다.
from uuid import uuid4

# 파일 확장자와 경로를 처리하기 위해 Path를 사용합니다.
from pathlib import Path

# FastAPI 핵심 클래스와 폼/파일 입력 도구를 가져옵니다.
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile

# API 응답을 JSON 객체로 명확하게 반환하기 위해 JSONResponse를 사용합니다.
from fastapi.responses import HTMLResponse, JSONResponse

# 정적 파일과 생성 결과 파일을 웹 URL로 제공하기 위해 StaticFiles를 사용합니다.
from fastapi.staticfiles import StaticFiles

# HTML 템플릿 렌더링을 위해 Jinja2Templates를 사용합니다.
from fastapi.templating import Jinja2Templates

# 애플리케이션 경로와 설정값을 가져옵니다.
from app.config import (
    AUDIO_DIR,
    GENERATED_DIR,
    STATIC_DIR,
    TEMPLATE_DIR,
    UPLOAD_DIR,
    settings,
)

# 각 기능의 서비스 함수를 가져옵니다.
from app.services.caption_service import generate_caption
from app.services.diffusion_service import generate_image
from app.services.speech_service import synthesize_speech, transcribe_audio


# FastAPI 애플리케이션 객체를 생성합니다.
app = FastAPI(
    title=settings.app_name,
    description="BLIP 한국어 이미지 캡셔닝, Stable Diffusion, PyTorch Whisper STT, TTS 통합 서비스",
    version="1.1.0",
    debug=settings.debug,
)

# 개발 중 이전 JavaScript가 브라우저 캐시에 남아 WebM을 전송하는 문제를 막기 위한 미들웨어입니다.
@app.middleware("http")
async def disable_static_cache(request: Request, call_next):
    """HTML과 정적 파일 응답에 캐시 금지 헤더를 추가합니다."""

    # 다음 FastAPI 처리 단계의 응답을 실행합니다.
    response = await call_next(request)

    # 메인 화면과 정적 파일은 항상 최신 소스를 다시 확인하도록 캐시를 비활성화합니다.
    if request.url.path == "/" or request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

    # 캐시 제어 헤더가 추가된 응답을 반환합니다.
    return response


# CSS와 JavaScript를 /static URL로 서비스합니다.
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 생성된 이미지를 /media/generated URL로 서비스합니다.
app.mount("/media/generated", StaticFiles(directory=GENERATED_DIR), name="generated")

# 생성된 TTS 파일을 /media/audio URL로 서비스합니다.
app.mount("/media/audio", StaticFiles(directory=AUDIO_DIR), name="audio")

# HTML 템플릿 디렉터리를 등록합니다.
templates = Jinja2Templates(directory=TEMPLATE_DIR)

# 이미지 캡셔닝에서 허용할 MIME 형식입니다.
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp"}

# STT는 브라우저에서 변환한 표준 PCM WAV만 받아 네이티브 코덱과 FFmpeg 의존성을 제거합니다.
ALLOWED_AUDIO_TYPES = {"audio/wav", "audio/x-wav"}


async def _save_upload(upload: UploadFile, allowed_types: set[str], category: str) -> Path:
    """업로드 형식과 크기를 검사한 뒤 고유 이름으로 저장합니다."""

    # 브라우저는 audio/webm;codecs=opus처럼 코덱 정보를 MIME 뒤에 붙여 보낼 수 있습니다.
    # 형식 비교 전 세미콜론 뒤의 파라미터를 제거하고 소문자로 정규화합니다.
    raw_content_type = (upload.content_type or "application/octet-stream").strip().lower()
    normalized_content_type = raw_content_type.split(";", 1)[0].strip()

    # 정규화한 기본 MIME 형식이 허용 목록에 없을 때만 요청을 거부합니다.
    if normalized_content_type not in allowed_types:
        raise HTTPException(
            status_code=415,
            detail=(
                f"지원하지 않는 {category} 형식입니다: {raw_content_type}. "
                f"허용 형식: {', '.join(sorted(allowed_types))}"
            ),
        )

    # 업로드 파일을 비동기로 읽습니다.
    content = await upload.read()

    # 설정에 정의한 최대 용량을 바이트 단위로 계산합니다.
    max_bytes = settings.max_upload_size_mb * 1024 * 1024

    # 파일 크기가 제한을 초과하면 메모리와 디스크 사용을 막기 위해 거부합니다.
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"파일은 {settings.max_upload_size_mb}MB 이하만 업로드할 수 있습니다.",
        )

    # 빈 파일은 모델 입력으로 사용할 수 없으므로 거부합니다.
    if not content:
        raise HTTPException(status_code=400, detail="업로드된 파일이 비어 있습니다.")

    # 원본 파일 확장자를 우선 사용하고, 확장자가 없으면 정규화한 MIME 형식에 맞춰 결정합니다.
    suffix = Path(upload.filename or "").suffix.lower()

    # MIME과 확장자의 대응표를 사용하면 audio/webm;codecs=opus 같은 값도 안전하게 저장할 수 있습니다.
    mime_suffix_map = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/bmp": ".bmp",
        "audio/webm": ".webm",
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/mpeg": ".mp3",
        "audio/mp4": ".m4a",
        "audio/ogg": ".ogg",
    }

    # 파일 이름에 확장자가 없는 경우에만 MIME 기반 확장자를 적용합니다.
    if not suffix:
        suffix = mime_suffix_map.get(normalized_content_type, ".bin")

    # 파일 이름에 사용자 입력을 직접 쓰지 않고 UUID를 사용해 경로 조작을 방지합니다.
    target_path = UPLOAD_DIR / f"{category}_{uuid4().hex}{suffix}"

    # 검증한 바이너리 데이터를 저장합니다.
    target_path.write_bytes(content)

    # 저장된 절대 경로를 반환합니다.
    return target_path


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    """두 AI 서비스를 선택할 수 있는 메인 웹 화면을 반환합니다."""

    # index.html에 애플리케이션 이름을 전달하여 렌더링합니다.
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"app_name": settings.app_name},
    )


@app.get("/api/health")
async def health() -> dict[str, str]:
    """서버 프로세스의 기본 동작 여부를 확인합니다."""

    # 모델을 미리 로딩하지 않고 API 서버만 정상인지 빠르게 확인합니다.
    return {"status": "ok", "message": "FastAPI server is running"}


@app.post("/api/caption")
async def caption_image(file: UploadFile = File(...)) -> JSONResponse:
    """업로드된 사진을 BLIP으로 분석하여 캡션을 반환합니다."""

    # 업로드 이미지를 검사하고 임시 저장합니다.
    image_path = await _save_upload(file, ALLOWED_IMAGE_TYPES, "image")

    try:
        # CPU 작업이 포함된 캡셔닝 서비스를 호출합니다.
        result = generate_caption(str(image_path))

        # 정상 결과를 JSON으로 반환합니다.
        return JSONResponse({"success": True, **result})
    except Exception as exc:
        # 모델 다운로드, 메모리, 손상 이미지 오류를 사용자에게 읽을 수 있는 형태로 전달합니다.
        raise HTTPException(status_code=500, detail=f"이미지 캡셔닝 실패: {exc}") from exc
    finally:
        # 캡셔닝이 끝난 업로드 원본을 삭제하여 디스크가 계속 증가하지 않게 합니다.
        image_path.unlink(missing_ok=True)


@app.post("/api/generate")
async def create_image(
    prompt: str = Form(...),
    negative_prompt: str = Form("blurry, low quality, distorted, watermark, text"),
    steps: int = Form(40),
    guidance_scale: float = Form(8.0),
    seed: int | None = Form(None),
) -> JSONResponse:
    """텍스트 또는 STT 결과 프롬프트로 Stable Diffusion 이미지를 생성합니다."""

    # 과도한 처리 시간을 막기 위해 생성 반복 횟수를 안전 범위로 제한합니다.
    if not 5 <= steps <= 60:
        raise HTTPException(status_code=422, detail="steps는 5에서 60 사이여야 합니다.")

    # 프롬프트 반영 강도를 일반적으로 유효한 범위로 제한합니다.
    if not 1.0 <= guidance_scale <= 20.0:
        raise HTTPException(status_code=422, detail="guidance_scale은 1.0에서 20.0 사이여야 합니다.")

    try:
        # Stable Diffusion 서비스를 호출해 결과 이미지와 시드를 받습니다.
        result = generate_image(prompt, negative_prompt, steps, guidance_scale, seed)

        # 프론트엔드가 이미지를 표시할 수 있도록 URL을 반환합니다.
        return JSONResponse({"success": True, **result})
    except torch_cuda_oom_error() as exc:
        # GPU 메모리 부족 시 해결 방향이 포함된 오류를 반환합니다.
        raise HTTPException(
            status_code=507,
            detail="GPU 메모리가 부족합니다. 다른 GPU 프로그램을 종료하거나 CPU 모드로 실행하세요.",
        ) from exc
    except Exception as exc:
        # 모델 접근 권한, 다운로드, 메모리 등의 상세 원인을 반환합니다.
        raise HTTPException(status_code=500, detail=f"이미지 생성 실패: {exc}") from exc


def torch_cuda_oom_error() -> type[BaseException]:
    """PyTorch 설치 여부에 관계없이 CUDA OOM 예외 클래스를 안전하게 반환합니다."""

    # 이 프로젝트의 필수 패키지인 torch를 함수 안에서 가져옵니다.
    import torch

    # 현재 PyTorch 버전의 OutOfMemoryError 클래스를 반환합니다.
    return torch.cuda.OutOfMemoryError


@app.post("/api/stt")
async def speech_to_text(file: UploadFile = File(...)) -> JSONResponse:
    """브라우저에서 녹음하거나 업로드한 음성을 한국어 텍스트로 변환합니다."""

    # 업로드 음성 형식과 크기를 검사한 뒤 저장합니다.
    audio_path = await _save_upload(file, ALLOWED_AUDIO_TYPES, "audio")

    try:
        # Whisper 기반 STT 서비스를 호출합니다.
        result = transcribe_audio(str(audio_path))

        # 인식 결과를 JSON으로 반환합니다.
        return JSONResponse({"success": True, **result})
    except Exception as exc:
        # 디코딩 실패나 음성 미감지 원인을 명확하게 전달합니다.
        raise HTTPException(status_code=500, detail=f"STT 변환 실패: {exc}") from exc
    finally:
        # 변환이 끝난 녹음 파일을 삭제합니다.
        audio_path.unlink(missing_ok=True)


@app.post("/api/tts")
async def text_to_speech(text: str = Form(...)) -> JSONResponse:
    """결과 문장을 운영체제 음성 엔진으로 합성하여 WAV URL을 반환합니다."""

    try:
        # 서버 측 TTS 서비스를 실행합니다.
        result = synthesize_speech(text)

        # 생성된 음성 URL을 반환합니다.
        return JSONResponse({"success": True, **result})
    except Exception as exc:
        # 시스템 음성 엔진이 없거나 저장에 실패한 경우 오류 원인을 반환합니다.
        raise HTTPException(status_code=500, detail=f"TTS 변환 실패: {exc}") from exc
