from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    앱 전체에서 공통으로 사용할 환경설정 클래스입니다.

    BaseSettings를 사용하면 .env 파일 또는 운영체제 환경변수에서
    설정값을 자동으로 읽어올 수 있습니다.
    """

    # FastAPI 문서와 브라우저 제목에 사용할 앱 이름입니다.
    APP_TITLE: str = "OpenAI Music Recommendation Chatbot"

    # 개발 모드 여부를 저장합니다.
    DEBUG: bool = True

    @field_validator("DEBUG", mode="before")
    @classmethod
    def normalize_debug(cls, value):
        if isinstance(value, str) and value.strip().lower() in {"release", "prod", "production"}:
            return False
        return value

    # OpenAI API 호출에 필요한 API Key입니다.
    OPENAI_API_KEY: str = ""

    # 기본 OpenAI 모델명입니다.
    # gpt-5.5를 기본값으로 두되, .env에서 다른 모델로 변경할 수 있습니다.
    OPENAI_MODEL: str = "gpt-5.5"

    # 일반 GPT 모델에서 사용할 창의성 조절값입니다.
    # 값이 높으면 다양한 답변을 생성하고, 낮으면 안정적인 답변을 생성합니다.
    OPENAI_TEMPERATURE: float = 0.7

    # 일반 GPT 모델에서 사용할 누적 확률 샘플링 값입니다.
    OPENAI_TOP_P: float = 0.95

    # OpenAI 응답의 최대 출력 토큰 수입니다.
    OPENAI_MAX_OUTPUT_TOKENS: int = 900

    # .env 파일을 읽도록 설정합니다.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Settings 객체를 한 번만 생성해서 재사용하는 함수입니다.

    lru_cache를 사용하면 요청이 들어올 때마다 .env 파일을 반복해서 읽지 않고
    이미 만들어진 설정 객체를 재사용할 수 있습니다.
    """
    return Settings()
