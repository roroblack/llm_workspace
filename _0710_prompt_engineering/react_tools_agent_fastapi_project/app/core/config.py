# -*- coding: utf-8 -*-
"""
FastAPI 앱 설정 모듈입니다.
.env 값을 직접 흩뿌리지 않고 Settings 객체 하나로 관리합니다.
"""

# pydantic의 BaseModel은 설정 값을 타입이 있는 객체로 관리하기 위해 사용합니다.
from pydantic import BaseModel

# common 모듈의 공통 경로와 모델명을 가져옵니다.
from common import DATA, DOCS, VECTOR_STORE, OPENAI_CHAT_MODEL, OPENAI_EMBEDDING_MODEL, GEMINI_MODEL, has_key


class Settings(BaseModel):
    """프로젝트 설정 값을 담는 Pydantic 모델입니다."""

    # 서비스 이름은 Swagger 문서와 health 응답에 표시됩니다.
    app_name: str = "Tools 기반 ReAct Agent FastAPI 프로젝트"

    # data 폴더 경로를 문자열로 보관합니다.
    data_dir: str = str(DATA)

    # docs 폴더 경로를 문자열로 보관합니다.
    docs_dir: str = str(DOCS)

    # Vector DB 저장 폴더 경로를 문자열로 보관합니다.
    vector_store_dir: str = str(VECTOR_STORE)

    # OpenAI 채팅 모델명을 보관합니다.
    openai_chat_model: str = OPENAI_CHAT_MODEL

    # OpenAI 임베딩 모델명을 보관합니다.
    openai_embedding_model: str = OPENAI_EMBEDDING_MODEL

    # Gemini 모델명을 보관합니다.
    gemini_model: str = GEMINI_MODEL

    # OpenAI API 키 설정 여부를 보관합니다.
    openai_ready: bool = has_key("OPENAI_API_KEY")

    # Gemini API 키 설정 여부를 보관합니다.
    gemini_ready: bool = has_key("GOOGLE_API_KEY")


# FastAPI 전체에서 공유할 설정 객체를 생성합니다.
settings = Settings()
