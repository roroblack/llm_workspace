"""
애플리케이션의 환경변수와 경로 설정을 한곳에서 관리합니다.
"""

# 설정 객체를 한 번만 생성하기 위해 lru_cache를 가져옵니다.
from functools import lru_cache

# 프로젝트 파일 경로를 안전하게 처리하기 위해 Path를 가져옵니다.
from pathlib import Path

# .env 기반 설정을 정의하기 위해 BaseSettings와 SettingsConfigDict를 가져옵니다.
from pydantic_settings import BaseSettings, SettingsConfigDict


# 이 파일의 상위 경로를 기준으로 프로젝트 루트 경로를 계산합니다.
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """
    .env 파일과 운영체제 환경변수에서 애플리케이션 설정을 읽는 클래스입니다.
    """

    # FastAPI 문서와 화면에 표시할 애플리케이션 이름입니다.
    app_name: str = "FastAPI RunPod LLM Evaluation"

    # mock은 로컬 모의 추론, transformers는 실제 모델 추론을 의미합니다.
    inference_backend: str = "mock"

    # 비교 기준이 되는 기반 모델의 Hugging Face 이름 또는 로컬 경로입니다.
    base_model_path: str = "Qwen/Qwen2.5-0.5B-Instruct"

    # 파인튜닝 후 병합한 모델의 Hugging Face 이름 또는 로컬 경로입니다.
    fine_tuned_model_path: str = "/workspace/models/merged_model"

    # Transformers가 모델을 GPU에 배치하는 방법입니다.
    device_map: str = "auto"

    # 모델 가중치에 사용할 자료형입니다.
    torch_dtype: str = "auto"

    # GPU 메모리를 절약하기 위한 4비트 양자화 사용 여부입니다.
    load_in_4bit: bool = False

    # 별도 값이 없을 때 사용할 최대 생성 토큰 수입니다.
    max_new_tokens: int = 256

    # 프로젝트 루트 기준 평가 데이터 파일 경로입니다.
    evaluation_file: str = "data/evaluation.jsonl"

    # 프로젝트 루트 기준 결과 저장 디렉터리입니다.
    output_dir: str = "outputs"

    # 웹 서버가 수신할 네트워크 주소입니다.
    host: str = "0.0.0.0"

    # 웹 서버가 사용할 포트 번호입니다.
    port: int = 8000

    # 비공개 Hugging Face 모델을 사용할 때 전달할 토큰입니다.
    hf_token: str | None = None

    # .env 파일의 설정을 읽고 알 수 없는 추가 값은 무시하도록 지정합니다.
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def evaluation_path(self) -> Path:
        """
        상대 경로로 설정된 평가 파일을 절대 경로로 변환합니다.
        """

        # 설정 문자열을 Path 객체로 변환합니다.
        configured_path = Path(self.evaluation_file)

        # 이미 절대 경로이면 그대로 반환합니다.
        if configured_path.is_absolute():
            return configured_path

        # 상대 경로이면 프로젝트 루트와 결합하여 반환합니다.
        return PROJECT_ROOT / configured_path

    @property
    def output_path(self) -> Path:
        """
        상대 경로로 설정된 출력 디렉터리를 절대 경로로 변환합니다.
        """

        # 설정 문자열을 Path 객체로 변환합니다.
        configured_path = Path(self.output_dir)

        # 절대 경로이면 그대로 사용합니다.
        if configured_path.is_absolute():
            return configured_path

        # 상대 경로이면 프로젝트 루트 아래의 경로로 변환합니다.
        return PROJECT_ROOT / configured_path


@lru_cache
def get_settings() -> Settings:
    """
    설정 객체를 한 번만 만들고 이후 호출에서는 같은 객체를 반환합니다.
    """

    # Settings 객체를 생성하여 반환합니다.
    return Settings()
