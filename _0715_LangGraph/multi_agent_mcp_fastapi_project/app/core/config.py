# -*- coding: utf-8 -*-
"""애플리케이션 전체에서 공유하는 환경설정 모듈입니다."""
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# 현재 파일 기준으로 프로젝트 루트 경로를 계산합니다.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    """`.env` 값을 타입이 있는 설정 객체로 변환합니다."""
    app_name: str = "Multi-Agent MCP RAG Assistant"
    app_version: str = "1.0.0"
    llm_provider: str = "gemini"
    database_url: str = "mysql+pymysql://multi_agent_user:multi_agent_password@127.0.0.1:3306/multi_agent_db?charset=utf8mb4"
    chroma_path: str = str(PROJECT_ROOT / "chroma_data")
    openai_model: str = "gpt-4o-mini"
    openai_embed_model: str = "text-embedding-3-small"
    gemini_model: str = "gemini-2.5-flash"
    gemini_embed_model: str = "models/gemini-embedding-001"
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", env_file_encoding="utf-8", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    """설정 객체를 한 번 생성한 뒤 재사용합니다."""
    return Settings()
