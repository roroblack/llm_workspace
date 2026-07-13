# -*- coding: utf-8 -*-
"""프로젝트 환경변수와 API Key 상태를 관리하는 설정 파일입니다."""

# 운영체제 환경변수를 읽기 위해 os 모듈을 불러옵니다.
import os

# 프로젝트 경로를 안전하게 계산하기 위해 pathlib 모듈을 불러옵니다.
from pathlib import Path

# .env 파일을 읽어 환경변수로 등록하기 위해 load_dotenv 함수를 불러옵니다.
from dotenv import load_dotenv

# 현재 파일 위치를 기준으로 프로젝트 최상위 폴더를 계산합니다.
ROOT_DIR = Path(__file__).resolve().parents[2]

# 프로젝트 최상위 폴더에 있는 .env 파일 경로를 지정합니다.
ENV_PATH = ROOT_DIR / ".env"

# .env 파일이 있으면 읽어서 환경변수로 등록합니다.
load_dotenv(ENV_PATH)

# 사용할 Gemini 모델명을 환경변수에서 읽고, 없으면 기본값을 사용합니다.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# 사용할 OpenAI 모델명을 환경변수에서 읽고, 없으면 기본값을 사용합니다.
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Gemini API Key를 환경변수에서 읽어 상수로도 참조할 수 있게 준비합니다.
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# OpenAI API Key를 환경변수에서 읽어 상수로도 참조할 수 있게 준비합니다.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def is_placeholder(value: str | None) -> bool:
    """환경변수 값이 비어 있거나 예시 문구인지 확인합니다."""

    # 값이 None이면 설정되지 않은 상태입니다.
    if value is None:
        return True

    # 앞뒤 공백을 제거한 문자열을 준비합니다.
    cleaned = value.strip()

    # 빈 문자열이면 설정되지 않은 상태입니다.
    if not cleaned:
        return True

    # 예시 파일의 안내 문구가 그대로 남아 있으면 실제 키가 아닙니다.
    if cleaned.startswith("여기에") or cleaned.startswith("선택_"):
        return True

    # 위 조건에 해당하지 않으면 실제 값이 입력된 것으로 판단합니다.
    return False


def require_env(name: str) -> str:
    """필수 환경변수가 없으면 실행자가 이해하기 쉬운 오류를 발생시킵니다."""

    # 지정한 이름의 환경변수 값을 읽습니다.
    value = os.getenv(name)

    # 값이 없거나 예시 문구이면 RuntimeError를 발생시킵니다.
    if is_placeholder(value):
        raise RuntimeError(
            f"{name} 값이 설정되어 있지 않습니다. .env.example을 .env로 복사한 뒤 실제 값을 입력하세요."
        )

    # 실제 환경변수 값을 반환합니다.
    return value.strip()


def get_env_status() -> dict:
    """현재 프로젝트 실행 환경 상태를 딕셔너리로 반환합니다."""

    # GOOGLE_API_KEY 설정 여부를 확인합니다.
    google_key_loaded = not is_placeholder(os.getenv("GOOGLE_API_KEY"))

    # OPENAI_API_KEY 설정 여부를 확인합니다.
    openai_key_loaded = not is_placeholder(os.getenv("OPENAI_API_KEY"))

    # 실행 환경 상태를 보기 좋게 반환합니다.
    return {
        "project_root": str(ROOT_DIR),
        "env_path": str(ENV_PATH),
        "env_file_exists": ENV_PATH.exists(),
        "gemini_model": GEMINI_MODEL,
        "openai_model": OPENAI_MODEL,
        "google_api_key_loaded": google_key_loaded,
        "openai_api_key_loaded": openai_key_loaded,
    }


# if __name__ == "__main__":
#     # 이 파일을 직접 실행하면 현재 환경 상태를 출력합니다.
#     status = get_env_status()
#     for key, value in status.items():
#         print(f"{key}: {value}")