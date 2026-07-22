# -*- coding: utf-8 -*-
"""제공된 common.py를 재사용하여 채팅 및 임베딩 모델을 생성하는 팩토리입니다."""

# Literal은 공급자 값을 openai 또는 gemini로 제한합니다.
from typing import Literal

# 제공된 공통 모듈의 모델 생성 함수를 가져옵니다.
from app.core.common import get_chat, get_embeddings
# 환경설정에서 temperature 값을 가져옵니다.
from app.core.settings import get_settings


# create_chat_model 함수는 common.py의 get_chat을 FastAPI 서비스 계층에 연결합니다.
def create_chat_model(provider: Literal["openai", "gemini"]):
    """선택 공급자의 LangChain 채팅 모델을 반환합니다."""
    # 공통 환경설정 객체를 읽습니다.
    settings = get_settings()
    # common.py에 공급자와 temperature를 전달하여 모델을 생성합니다.
    return get_chat(provider=provider, temperature=settings.temperature)


# create_embeddings 함수는 common.py의 get_embeddings를 RAG 서비스에 연결합니다.
def create_embeddings(provider: Literal["openai", "gemini"]):
    """선택 공급자의 LangChain 임베딩 모델을 반환합니다."""
    # common.py가 API 키 검증과 모델명 선택을 공통 처리합니다.
    return get_embeddings(provider=provider)
