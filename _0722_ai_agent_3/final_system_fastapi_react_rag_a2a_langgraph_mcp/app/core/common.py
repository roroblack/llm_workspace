# -*- coding: utf-8 -*-
"""제공된 common.py를 FastAPI 앱 구조에 맞게 경로만 조정한 공통 모듈입니다."""

# os는 운영체제 환경변수에서 API 키와 모델명을 읽습니다.
import os
# pathlib.Path는 Windows와 macOS/Linux에서 동일한 방식으로 경로를 다룹니다.
from pathlib import Path

# load_dotenv는 프로젝트 루트의 .env 파일을 환경변수로 로드합니다.
from dotenv import load_dotenv

# 현재 파일은 app/core/common.py이므로 parents[2]가 프로젝트 루트입니다.
ROOT = Path(__file__).resolve().parents[2]
# DATA는 data.zip에서 추출한 실데이터 폴더 경로입니다.
DATA = ROOT / "data"
# DOCS는 RAG에서 사용할 정책 PDF 폴더 경로입니다.
DOCS = DATA / "docs"

# 프로젝트 루트의 .env 파일을 UTF-8 환경변수로 로드합니다.
load_dotenv(ROOT / ".env")

# GEMINI_MODEL은 환경변수 값이 없을 때 기본 Gemini 채팅 모델을 사용합니다.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
# GEMINI_EMBED_MODEL은 정책 PDF 벡터화에 사용할 Gemini 임베딩 모델입니다.
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "models/gemini-embedding-001")
# OPENAI_MODEL은 환경변수 값이 없을 때 기본 OpenAI 채팅 모델을 사용합니다.
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
# OPENAI_EMBED_MODEL은 정책 PDF 벡터화에 사용할 OpenAI 임베딩 모델입니다.
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")


# require_key 함수는 필수 API 키가 실제로 설정되어 있는지 검사합니다.
def require_key(name: str) -> str:
    """환경변수 키가 없거나 예제 문자열이면 명확한 설정 오류를 발생시킵니다."""
    # 요청한 이름의 환경변수 값을 읽습니다.
    value = os.getenv(name, "").strip()
    # 값이 비어 있거나 예제 문구로 시작하면 유효하지 않은 키로 판단합니다.
    if not value or value.startswith("여기에"):
        # FastAPI에서 처리 가능한 ValueError로 필요한 조치를 안내합니다.
        raise ValueError(
            f"{name}가 .env에 설정되지 않았습니다. "
            ".env.example을 .env로 복사한 뒤 실제 API 키를 입력하세요."
        )
    # 검증된 키 문자열을 반환합니다.
    return value


# get_genai_client 함수는 Google의 원시 SDK 클라이언트를 생성합니다.
def get_genai_client():
    """Google Gemini 원시 SDK 클라이언트를 반환합니다."""
    # google.genai는 실제 사용 시에만 지연 import합니다.
    from google import genai
    # 검증된 Google API 키로 클라이언트를 생성합니다.
    return genai.Client(api_key=require_key("GOOGLE_API_KEY"))


# get_chat 함수는 OpenAI 또는 Gemini LangChain 채팅 모델을 통일된 방식으로 생성합니다.
def get_chat(provider: str = "gemini", temperature: float = 0.0):
    """provider 값에 맞는 LangChain ChatModel을 반환합니다."""
    # Gemini 공급자를 선택했는지 확인합니다.
    if provider == "gemini":
        # Google API 키를 먼저 검증합니다.
        api_key = require_key("GOOGLE_API_KEY")
        # Gemini 전용 LangChain 클래스를 지연 import합니다.
        from langchain_google_genai import ChatGoogleGenerativeAI
        # 환경변수 모델명과 temperature로 Gemini 모델을 생성합니다.
        return ChatGoogleGenerativeAI(
            google_api_key=api_key,
            model=GEMINI_MODEL,
            temperature=temperature,
            max_retries=0,
        )
    # OpenAI 공급자를 선택했는지 확인합니다.
    if provider == "openai":
        # OpenAI API 키를 먼저 검증합니다.
        api_key = require_key("OPENAI_API_KEY")
        # OpenAI 전용 LangChain 클래스를 지연 import합니다.
        from langchain_openai import ChatOpenAI
        # 환경변수 모델명과 temperature로 OpenAI 모델을 생성합니다.
        return ChatOpenAI(
            api_key=api_key,
            model=OPENAI_MODEL,
            temperature=temperature,
            max_retries=0,
        )
    # 지원하지 않는 공급자는 잘못된 입력으로 처리합니다.
    raise ValueError(f"알 수 없는 provider입니다: {provider}")


# get_embeddings 함수는 선택한 공급자의 임베딩 모델을 통일된 방식으로 생성합니다.
def get_embeddings(provider: str = "gemini"):
    """provider 값에 맞는 LangChain Embeddings 객체를 반환합니다."""
    # Gemini 임베딩을 선택했는지 확인합니다.
    if provider == "gemini":
        # Google API 키를 검증합니다.
        api_key = require_key("GOOGLE_API_KEY")
        # Gemini 임베딩 클래스를 지연 import합니다.
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        # 검색 속도와 저장 크기를 고려해 768차원 임베딩을 사용합니다.
        return GoogleGenerativeAIEmbeddings(
            google_api_key=api_key,
            model=GEMINI_EMBED_MODEL,
            output_dimensionality=768,
        )
    # OpenAI 임베딩을 선택했는지 확인합니다.
    if provider == "openai":
        # OpenAI API 키를 검증합니다.
        api_key = require_key("OPENAI_API_KEY")
        # OpenAI 임베딩 클래스를 지연 import합니다.
        from langchain_openai import OpenAIEmbeddings
        # 환경변수로 지정한 OpenAI 임베딩 모델을 생성합니다.
        return OpenAIEmbeddings(api_key=api_key, model=OPENAI_EMBED_MODEL)
    # 지원하지 않는 공급자는 오류로 처리합니다.
    raise ValueError(f"알 수 없는 provider입니다: {provider}")


# 파일을 직접 실행하면 공통 경로와 API 키 로드 상태를 확인합니다.
if __name__ == "__main__":
    # 실행 단계 확인도 공용 구조적 logger로 기록합니다.
    from app.core.logging_config import setup_logging

    logger = setup_logging()
    logger.info("ROOT: %s", ROOT)
    logger.info("DATA: %s 존재=%s", DATA, DATA.exists())
    logger.info("DOCS: %s 존재=%s", DOCS, DOCS.exists())
    logger.info(
        "API 키 설정 상태: GOOGLE_API_KEY=%s OPENAI_API_KEY=%s",
        bool(os.getenv("GOOGLE_API_KEY")),
        bool(os.getenv("OPENAI_API_KEY")),
    )
