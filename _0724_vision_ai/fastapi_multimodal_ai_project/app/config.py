"""애플리케이션 전체에서 공통으로 사용하는 설정 값을 관리하는 모듈입니다."""

# 표준 라이브러리의 Path 클래스를 사용하여 운영체제에 안전한 파일 경로를 구성합니다.
from pathlib import Path

# Pydantic Settings를 사용하여 .env 파일과 운영체제 환경 변수를 읽습니다.
from pydantic_settings import BaseSettings, SettingsConfigDict


# 프로젝트 최상위 디렉터리의 절대 경로를 계산합니다.
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """환경 변수로 변경할 수 있는 애플리케이션 설정 모델입니다."""

    # FastAPI 문서와 브라우저 제목에 사용할 서비스 이름입니다.
    app_name: str = "Image Captioning & Stable Diffusion Voice Studio"

    # 개발 환경에서 자세한 오류 확인 여부를 지정합니다.
    debug: bool = True

    # 이미지 캡셔닝에 사용할 Hugging Face BLIP 모델 식별자입니다.
    caption_model_id: str = "Salesforce/blip-image-captioning-base"

    # BLIP 영어 캡션의 객체와 행동을 보존해 한국어로 번역할 NLLB 모델 식별자입니다.
    translation_model_id: str = "facebook/nllb-200-distilled-600M"

    # 텍스트를 이미지로 변환할 Stable Diffusion 모델 식별자입니다.
    diffusion_model_id: str = "stabilityai/stable-diffusion-xl-base-1.0"

    # 한국어 음성 인식에 사용할 Hugging Face Whisper 모델 식별자입니다.
    # CTranslate2 네이티브 DLL을 사용하는 faster-whisper 대신 PyTorch 기반 모델을 사용합니다.
    whisper_model_id: str = "openai/whisper-small"

    # 한 번에 업로드할 수 있는 파일의 최대 크기를 15MB로 제한합니다.
    max_upload_size_mb: int = 15

    # 기본 이미지 생성 반복 횟수입니다. 값이 클수록 일반적으로 품질은 향상되지만 느려집니다.
    default_inference_steps: int = 40

    # 기본 프롬프트 반영 강도입니다.
    default_guidance_scale: float = 8.0

    # SDXL 기본 학습 해상도입니다. 메모리가 부족하면 .env에서 768로 낮출 수 있습니다.
    diffusion_image_size: int = 1024

    # .env 파일을 UTF-8로 읽고 정의되지 않은 추가 값은 무시합니다.
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# 다른 모듈에서 재사용할 단일 설정 객체를 생성합니다.
settings = Settings()

# 업로드 파일 저장 경로를 정의합니다.
UPLOAD_DIR = BASE_DIR / "storage" / "uploads"

# Stable Diffusion 결과 이미지 저장 경로를 정의합니다.
GENERATED_DIR = BASE_DIR / "storage" / "generated"

# TTS 음성 파일 저장 경로를 정의합니다.
AUDIO_DIR = BASE_DIR / "storage" / "audio"

# 정적 HTML, CSS, JavaScript 파일 경로를 정의합니다.
STATIC_DIR = BASE_DIR / "app" / "static"

# Jinja2 HTML 템플릿 파일 경로를 정의합니다.
TEMPLATE_DIR = BASE_DIR / "app" / "templates"

# 필요한 저장 디렉터리가 없으면 서버 시작 시 자동으로 생성합니다.
for directory in (UPLOAD_DIR, GENERATED_DIR, AUDIO_DIR):
    directory.mkdir(parents=True, exist_ok=True)
