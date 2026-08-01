"""프로젝트 전체 환경 설정을 정의합니다."""

# 운영체제 환경변수를 읽기 위해 os 모듈을 가져옵니다.
import os
# 경로를 안전하게 처리하기 위해 Path 클래스를 가져옵니다.
from pathlib import Path
# 설정값을 객체 형태로 관리하기 위해 dataclass를 가져옵니다.
from dataclasses import dataclass


# 변경 불가능한 공통 설정 객체를 만들기 위해 dataclass를 적용합니다.
@dataclass(frozen=True)
class Settings:
    """FastAPI, 조건부 GAN, STT 실행에 필요한 설정값을 보관합니다."""

    # 현재 파일에서 프로젝트 최상위 디렉터리를 계산합니다.
    project_root: Path = Path(__file__).resolve().parents[2]
    # HTML 템플릿 저장 경로를 지정합니다.
    templates_dir: Path = project_root / "app" / "templates"
    # CSS와 JavaScript 정적 파일 경로를 지정합니다.
    static_dir: Path = project_root / "app" / "static"
    # MNIST 데이터 저장 경로를 지정합니다.
    data_dir: Path = project_root / "data"
    # 녹음 음성 저장 경로를 지정합니다.
    audio_dir: Path = project_root / "storage" / "audio"
    # STT 텍스트 저장 경로를 지정합니다.
    transcript_dir: Path = project_root / "storage" / "transcripts"
    # 에포크별 생성 이미지 저장 경로를 지정합니다.
    generation_dir: Path = project_root / "storage" / "generations"
    # 학습 모델 저장 경로를 지정합니다.
    model_dir: Path = project_root / "storage" / "models"
    # 애플리케이션 이름을 지정합니다.
    app_name: str = "Prompt & Voice Conditional GAN"
    # 생성자의 잠재 벡터 차원을 환경변수 또는 기본값으로 설정합니다.
    latent_dim: int = int(os.getenv("GAN_LATENT_DIM", "100"))
    # 미니배치 크기를 환경변수 또는 기본값으로 설정합니다.
    batch_size: int = int(os.getenv("GAN_BATCH_SIZE", "128"))
    # GAN 학습률을 환경변수 또는 기본값으로 설정합니다.
    learning_rate: float = float(os.getenv("GAN_LEARNING_RATE", "0.0002"))
    # Adam 첫 번째 모멘텀 계수를 설정합니다.
    beta1: float = float(os.getenv("GAN_BETA1", "0.5"))
    # Adam 두 번째 모멘텀 계수를 설정합니다.
    beta2: float = float(os.getenv("GAN_BETA2", "0.999"))
    # 빠른 실습을 위해 사용할 MNIST 최대 샘플 수를 설정합니다.
    max_training_samples: int = int(os.getenv("GAN_MAX_TRAINING_SAMPLES", "10000"))
    # Windows PyCharm 환경에서 안정적인 DataLoader 프로세스 수를 설정합니다.
    num_workers: int = int(os.getenv("GAN_NUM_WORKERS", "0"))
    # Whisper 모델 크기를 설정합니다. CPU 실습 환경을 고려해 base를 기본값으로 사용합니다.
    whisper_model_size: str = os.getenv("WHISPER_MODEL_SIZE", "base")
    # STT 실행 장치를 자동 또는 수동으로 설정합니다.
    whisper_device: str = os.getenv("WHISPER_DEVICE", "auto")
    # CPU 환경의 faster-whisper 계산 형식을 설정합니다.
    whisper_compute_type_cpu: str = os.getenv("WHISPER_COMPUTE_TYPE_CPU", "int8")
    # CUDA 환경의 faster-whisper 계산 형식을 설정합니다.
    whisper_compute_type_cuda: str = os.getenv("WHISPER_COMPUTE_TYPE_CUDA", "float16")
    # STT 작업자 최대 실행 시간을 초 단위로 설정합니다. 최초 모델 다운로드 시간을 고려해 900초를 사용합니다.
    stt_timeout_seconds: int = int(os.getenv("STT_TIMEOUT_SECONDS", "900"))
    # 너무 짧은 녹음 업로드를 차단할 최소 바이트 수를 설정합니다.
    minimum_audio_bytes: int = int(os.getenv("STT_MINIMUM_AUDIO_BYTES", "1000"))
    # 저장 파일을 브라우저에 노출할 URL 접두사를 지정합니다.
    storage_url_prefix: str = "/storage"

    def create_directories(self) -> None:
        """애플리케이션 실행에 필요한 디렉터리를 생성합니다."""
        # 생성 대상 경로를 순서대로 반복합니다.
        for directory in (
            self.data_dir,
            self.audio_dir,
            self.transcript_dir,
            self.generation_dir,
            self.model_dir,
        ):
            # 경로가 없으면 상위 경로까지 포함하여 생성합니다.
            directory.mkdir(parents=True, exist_ok=True)


# 애플리케이션 전체에서 공유할 설정 객체를 생성합니다.
settings = Settings()
