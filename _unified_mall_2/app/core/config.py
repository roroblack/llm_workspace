"""애플리케이션 설정 (단일 소스).

RULE.md 3.1(하드코딩 금지)에 따라 모델명·경로·키·DB 접속정보를 모두 여기로 모은다.
값은 .env 또는 환경변수에서 로드한다. 기본 프로바이더는 로컬 Gemma(llama-cpp-python
OpenAI 호환 서버)로, 빌드 중 외부 토큰을 소모하지 않는다.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# 프로젝트 루트: 이 파일은 app/core/config.py 이므로 parents[2] = 프로젝트 루트
ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """전 계층이 공유하는 설정값."""

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM 프로바이더 선택 ---
    LLM_PROVIDER: Literal["local", "openai", "gemini"] = "local"

    # --- 모델 레지스트리(Phase 1) ---
    # 활성 모델 '프로필 선택자'(모델 ID 자체가 아니라 model_registry.yaml의 profile_id).
    # 실제 모델 ID·revision·checksum은 model_registry.yaml에서 해석한다(RULE 3.1: 소스 모델ID 금지).
    ACTIVE_MODEL_PROFILE: str = "local_gemma4_e4b"

    # --- 로컬(Gemma GGUF, OpenAI 호환 서버) ---
    LOCAL_BASE_URL: str = "http://127.0.0.1:8000/v1"
    LOCAL_MODEL: str = "gemma-4-e4b"
    LOCAL_API_KEY: str = "not-needed"

    # --- OpenAI ---
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # --- Gemini ---
    GOOGLE_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # --- pgvector (Phase 3, 학습 트랙) ---
    # 접속 정보(모델ID 아님) — userspace PG(conda pgv env). 미기동이면 접속 실패→명시 오류(무폴백).
    PGVECTOR_DSN: str = "host=127.0.0.1 port=5433 user=postgres dbname=mall_vec"

    # --- RAG / 임베딩 ---
    EMBEDDING_PROVIDER: Literal["local_st"] = "local_st"
    ST_EMBEDDING_MODEL: str = "jhgan/ko-sroberta-multitask"
    CHUNK_SIZE: int = 400
    CHUNK_OVERLAP: int = 50
    RAG_TOP_K: int = 3
    # 임베딩 정규화 시 거리는 [0,2] 범위 → 이 값 초과는 무관으로 간주(방어)
    RAG_MAX_DISTANCE: float = 1.5

    # --- ML (감성분석) ---
    SENTIMENT_MODEL: str = "monologg/koelectra-base-finetuned-nsmc"
    SENTIMENT_DEVICE: int = -1  # -1=CPU

    # --- 음성 (Phase 11, STT/TTS) ---
    # GPU 미검출 환경(Codex 검토) — CPU + int8로 검증한 크기만 기본값으로 둔다.
    STT_MODEL: str = "small"
    STT_DEVICE: str = "cpu"
    STT_COMPUTE_TYPE: str = "int8"
    STT_LANGUAGE: str = "ko"
    # SAPI5 보이스 ID 부분 문자열로 찾는다(전체 ID는 OS마다 다름) — 없으면 ConfigError.
    TTS_VOICE_MATCH: str = "KO-KR"

    # --- Lab (비용 추정) ---
    # 1M 토큰당 USD [input, output]. 로컬(local)은 과금 없음이라 미등록 → 비용추정 불가.
    PRICE_TABLE: dict[str, list[float]] = {
        "gpt-4o-mini": [0.15, 0.60],
        "gemini-2.5-flash": [0.075, 0.30],
    }

    # --- 경로 / DB ---
    DATA_DIR: Path = ROOT_DIR / "data"
    DOCS_DIR: Path = ROOT_DIR / "data" / "docs"
    VECTOR_DIR: Path = ROOT_DIR / "data" / "vector_store"
    # CWD 의존을 피하기 위해 절대 경로 기반 (Codex 합의)
    DATABASE_URL: str = f"sqlite:///{(ROOT_DIR / 'data' / 'mall.db').as_posix()}"

    # --- 인증 (JWT) ---
    # SECRET_KEY는 하드코딩 금지: 미설정이면 auth 사용 시 ConfigError (RULE 3.1/3.2)
    SECRET_KEY: str | None = None
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    def require_secret_key(self) -> str:
        if not (self.SECRET_KEY and self.SECRET_KEY.strip()):
            from app.core.errors import ConfigError

            raise ConfigError("SECRET_KEY가 설정되지 않았습니다. .env에 SECRET_KEY를 넣으세요.")
        return self.SECRET_KEY

    def has_openai_key(self) -> bool:
        return bool(self.OPENAI_API_KEY and self.OPENAI_API_KEY.strip())

    def has_google_key(self) -> bool:
        return bool(self.GOOGLE_API_KEY and self.GOOGLE_API_KEY.strip())

    def readiness(self) -> dict[str, bool]:
        """LLM 실호출 없이 '설정/키/경로 존재 여부'만 보고한다 (Codex 합의)."""
        return {
            "local": self.LLM_PROVIDER == "local" and bool(self.LOCAL_BASE_URL),
            "openai": self.has_openai_key(),
            "gemini": self.has_google_key(),
            "db": bool(self.DATABASE_URL),
            "vector": self.VECTOR_DIR.exists(),
        }


@lru_cache
def get_settings() -> Settings:
    """설정 싱글턴. 테스트에서 환경 변경 시 get_settings.cache_clear() 사용."""
    return Settings()
