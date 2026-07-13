# -*- coding: utf-8 -*-
"""
app/common.py — FastAPI LLM 실습 공통 파일

목적:
  - 프로젝트 루트의 .env 파일에서 API Key를 읽습니다.
  - Gemini API 클라이언트를 한 곳에서 생성합니다.
  - OpenAI API Key 사용 여부를 확인합니다.
  - FastAPI 라우터에서 공통으로 사용할 모델 이름을 관리합니다.

주의:
  - GOOGLE_API_KEY는 .env 파일에 직접 작성해야 합니다.
  - 실제 API Key는 GitHub에 올리면 안 됩니다.
"""

# 운영체제 환경변수 값을 읽기 위해 os 모듈을 불러옵니다.
import os

# 파일 경로를 안전하게 다루기 위해 pathlib 모듈을 불러옵니다.
import pathlib

# .env 파일을 읽어 환경변수로 등록하기 위해 load_dotenv 함수를 불러옵니다.
from dotenv import load_dotenv

# 현재 파일(app/common.py)을 기준으로 프로젝트 루트 폴더를 계산합니다.
ROOT = pathlib.Path(__file__).resolve().parents[1]

# 프로젝트 루트 아래 data 폴더 경로를 지정합니다.
DATA = ROOT / "data"

# 프로젝트 루트 아래 data/docs 폴더 경로를 지정합니다.
DOCS = DATA / "docs"

# 프로젝트 루트에 있는 .env 파일을 읽어 환경변수로 등록합니다.
load_dotenv(ROOT / ".env")

# 사용할 Gemini 모델명을 환경변수에서 읽고, 없으면 기본값을 사용합니다.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# 사용할 Gemini 임베딩 모델명을 환경변수에서 읽고, 없으면 기본값을 사용합니다.
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "models/gemini-embedding-001")


def get_env_status() -> dict:
    """현재 프로젝트의 환경 설정 상태를 딕셔너리로 반환합니다."""

    # GOOGLE_API_KEY가 설정되어 있는지 확인합니다.
    google_key_exists = bool(os.getenv("GOOGLE_API_KEY"))

    # OPENAI_API_KEY가 설정되어 있는지 확인합니다.
    openai_key_exists = bool(os.getenv("OPENAI_API_KEY"))

    # 프로젝트 루트, 데이터 폴더, 모델명, 키 설정 여부를 반환합니다.
    return {
        "root": str(ROOT),
        "data_dir": str(DATA),
        "data_dir_exists": DATA.exists(),
        "gemini_model": GEMINI_MODEL,
        "google_api_key_loaded": google_key_exists,
        "openai_api_key_loaded": openai_key_exists,
    }


def require_key(name: str) -> str:
    """필수 API Key가 없으면 명확한 오류 메시지를 발생시킵니다."""

    # 환경변수에서 지정한 이름의 값을 읽습니다.
    value = os.getenv(name)

    # 값이 없거나 예시 문구 그대로이면 설정 오류로 판단합니다.
    if not value or value.startswith("여기에"):
        raise RuntimeError(
            f"[설정 필요] {name} 값이 .env 파일에 없습니다. "
            f".env.example을 복사해 .env를 만든 뒤 {name} 값을 입력하세요."
        )

    # 정상 설정된 API Key 값을 반환합니다.
    return value


def get_genai_client():
    """google-genai Gemini 클라이언트를 생성해 반환합니다."""

    # google-genai 패키지에서 genai 모듈을 불러옵니다.
    from google import genai

    # GOOGLE_API_KEY 값을 확인합니다.
    api_key = require_key("GOOGLE_API_KEY")

    # API Key를 사용해 Gemini 클라이언트를 생성합니다.
    return genai.Client(api_key=api_key)
