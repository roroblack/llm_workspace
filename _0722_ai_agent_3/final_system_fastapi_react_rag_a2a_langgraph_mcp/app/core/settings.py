# -*- coding: utf-8 -*-
"""애플리케이션 환경설정과 경로를 한 곳에서 관리하는 모듈입니다."""

# functools.lru_cache는 설정 객체를 한 번만 생성하여 반복 로딩을 막습니다.
from functools import lru_cache
# pathlib.Path는 운영체제에 독립적인 파일 경로를 안전하게 다룹니다.
from pathlib import Path
# typing.Literal은 허용 가능한 공급자 문자열을 제한합니다.
from typing import Literal

# pydantic의 Field는 환경변수 기본값과 설명을 정의합니다.
from pydantic import Field
# pydantic-settings는 .env와 시스템 환경변수를 Pydantic 모델로 읽습니다.
from pydantic_settings import BaseSettings, SettingsConfigDict

# 현재 파일의 상위 경로를 기준으로 프로젝트 루트 경로를 계산합니다.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
# data.zip에서 추출한 데이터 파일이 위치하는 경로를 정의합니다.
DATA_DIR = PROJECT_ROOT / "data"
# 정책 PDF 문서가 위치하는 하위 폴더 경로를 정의합니다.
DOCS_DIR = DATA_DIR / "docs"
# 로그 파일을 저장할 폴더 경로를 정의합니다.
LOG_DIR = PROJECT_ROOT / "logs"
# FAISS 인덱스와 기타 캐시를 저장할 폴더 경로를 정의합니다.
CACHE_DIR = PROJECT_ROOT / "cache"
# 생성된 요약·매출 보고서를 저장할 폴더입니다.
REPORTS_DIR = PROJECT_ROOT / "reports"


# Settings 클래스는 애플리케이션에서 사용할 모든 환경변수를 타입 안전하게 관리합니다.
class Settings(BaseSettings):
    """FastAPI, LLM, RAG, 재시도 설정을 보관하는 환경설정 모델입니다."""

    # model_config는 .env 파일을 읽고 알 수 없는 키는 무시하도록 설정합니다.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # app_name은 Swagger와 웹 화면에 표시할 애플리케이션 이름입니다.
    app_name: str = Field(default="승승장구몰 통합 CS Agent")
    # app_version은 API 버전을 표시합니다.
    app_version: str = Field(default="1.0.0")
    # 운영체제의 범용 DEBUG 변수와 충돌하지 않도록 APP_DEBUG만 읽습니다.
    app_debug: bool = Field(default=True, alias="APP_DEBUG")
    # default_provider는 별도 지정이 없을 때 사용할 LLM 공급자입니다.
    default_provider: Literal["openai", "gemini"] = Field(default="openai")

    # openai_api_key는 OpenAI API 인증 키를 저장합니다.
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    # openai_model은 OpenAI 채팅 모델 이름입니다.
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    # openai_embed_model은 OpenAI 임베딩 모델 이름입니다.
    openai_embed_model: str = Field(default="text-embedding-3-small", alias="OPENAI_EMBED_MODEL")

    # google_api_key는 Gemini API 인증 키를 저장합니다.
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    # gemini_model은 Gemini 채팅 모델 이름입니다.
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    # gemini_embed_model은 Gemini 임베딩 모델 이름입니다.
    gemini_embed_model: str = Field(default="models/gemini-embedding-001", alias="GEMINI_EMBED_MODEL")

    # temperature는 답변의 무작위성을 제어합니다.
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    # max_retries는 외부 LLM 호출 실패 시 최대 재시도 횟수입니다.
    max_retries: int = Field(default=3, ge=1, le=10)
    # retry_base_seconds는 지수 백오프의 최초 대기 시간입니다.
    retry_base_seconds: float = Field(default=0.5, ge=0.0)

    # rag_chunk_size는 PDF 문서를 자를 청크 크기입니다.
    rag_chunk_size: int = Field(default=700, ge=100)
    # rag_chunk_overlap은 인접 청크 사이의 중첩 길이입니다.
    rag_chunk_overlap: int = Field(default=100, ge=0)
    # rag_top_k는 질문과 가장 관련된 상위 문서 개수입니다.
    rag_top_k: int = Field(default=4, ge=1, le=20)

    # cors_origins는 개발용 브라우저 접근을 허용할 출처 목록입니다.
    cors_origins: list[str] = Field(default=["*"])

    # 고객 문의를 저장할 MySQL fastapi_db 연결 설정입니다.
    mysql_host: str = Field(default="127.0.0.1", alias="MYSQL_HOST")
    mysql_port: int = Field(default=3306, alias="MYSQL_PORT", ge=1, le=65535)
    mysql_user: str = Field(default="root", alias="MYSQL_USER")
    mysql_password: str = Field(default="", alias="MYSQL_PASSWORD")
    mysql_database: str = Field(default="fastapi_db", alias="MYSQL_DATABASE")
    mysql_connect_timeout: int = Field(default=5, alias="MYSQL_CONNECT_TIMEOUT", ge=1, le=60)


# lru_cache는 Settings 객체를 프로세스에서 한 번만 생성합니다.
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """캐시된 환경설정 객체를 반환합니다."""
    # Settings 생성 시 .env와 시스템 환경변수를 자동으로 읽습니다.
    return Settings()
