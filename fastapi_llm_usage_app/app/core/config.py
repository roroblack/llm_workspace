# 운영체제 환경변수를 읽기 위해 os 모듈을 가져옵니다.
import os

# .env 파일의 값을 환경변수로 등록하기 위해 load_dotenv 함수를 가져옵니다.
from dotenv import load_dotenv

# Pydantic 기반 설정 클래스를 만들기 위해 BaseSettings를 가져옵니다.
from pydantic_settings import BaseSettings

# .env 파일을 현재 프로세스의 환경변수로 로드합니다.
load_dotenv()


# 프로젝트 전체에서 사용할 설정값을 한 곳에서 관리하는 클래스입니다.
class Settings(BaseSettings):
    # OpenAI API 호출에 사용할 API Key입니다.
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")

    # Gemini API 호출에 사용할 API Key입니다.
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")

    # OpenAI 호출에 사용할 기본 모델명입니다.
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5.5")

    # Gemini 호출에 사용할 기본 모델명입니다.
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # 생성 결과의 다양성을 조절하는 기본 temperature 값입니다.
    default_temperature: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))

    # 후보 토큰 누적 확률 범위를 조절하는 기본 top_p 값입니다.
    default_top_p: float = float(os.getenv("DEFAULT_TOP_P", "0.95"))

    # 모델이 생성할 수 있는 최대 출력 토큰 수입니다.
    default_max_output_tokens: int = int(os.getenv("DEFAULT_MAX_OUTPUT_TOKENS", "800"))

    # API 요청이 너무 오래 걸릴 때 중단하기 위한 기본 제한 시간입니다.
    default_timeout_seconds: int = int(os.getenv("DEFAULT_TIMEOUT_SECONDS", "60"))


# 앱 어디서나 import 하여 사용할 설정 객체를 생성합니다.
settings = Settings()
