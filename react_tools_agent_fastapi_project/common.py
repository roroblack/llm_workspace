# -*- coding: utf-8 -*-
"""
common.py — 프로젝트 전체 공통 모듈

이 파일은 이전 실습에서 사용한 common.py 구조를 FastAPI 프로젝트용으로 확장한 공통 모듈입니다.
목적:
  1) .env 파일의 API 키와 모델명을 한 곳에서 로드합니다.
  2) OpenAI, Gemini, LangChain ChatModel 생성 코드를 한 곳에 모읍니다.
  3) data/, vector_store/ 같은 공통 경로를 전역 상수로 제공합니다.
"""

# 표준 라이브러리 os는 환경변수를 읽기 위해 사용합니다.
import os

# pathlib.Path는 운영체제별 경로 구분자를 안전하게 처리하기 위해 사용합니다.
from pathlib import Path

# python-dotenv의 load_dotenv는 .env 파일을 읽어 환경변수로 등록합니다.
from dotenv import load_dotenv


# ROOT는 현재 common.py 파일이 있는 프로젝트 루트 경로입니다.
ROOT = Path(__file__).resolve().parent

# DATA는 CSV와 문서 파일을 보관하는 data 폴더 경로입니다.
DATA = ROOT / "data"

# DOCS는 Vector DB에 넣을 텍스트 문서 폴더 경로입니다.
DOCS = DATA / "docs"

# VECTOR_STORE는 로컬 Vector DB 저장 파일을 보관하는 폴더 경로입니다.
VECTOR_STORE = ROOT / "vector_store"

# 루트의 .env 파일을 읽어 OPENAI_API_KEY, GOOGLE_API_KEY 등을 환경변수에 올립니다.
load_dotenv(ROOT / ".env")


# OpenAI 채팅 모델명은 .env에서 읽고, 없으면 gpt-4o-mini를 기본값으로 사용합니다.
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

# OpenAI 임베딩 모델명은 .env에서 읽고, 없으면 text-embedding-3-small을 기본값으로 사용합니다.
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# Gemini 모델명은 .env에서 읽고, 없으면 gemini-2.5-flash를 기본값으로 사용합니다.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def get_env(name: str, default: str = "") -> str:
    """환경변수를 안전하게 읽어오는 함수입니다."""
    # os.getenv은 환경변수가 없을 때 None을 반환할 수 있으므로 default를 지정합니다.
    return os.getenv(name, default)


def has_key(name: str) -> bool:
    """API 키가 .env에 실제로 설정되어 있는지 True/False로 확인합니다."""
    # 환경변수 값을 읽습니다.
    value = os.getenv(name)

    # 값이 없거나 예시 문자열이면 실제 키가 아니므로 False를 반환합니다.
    return bool(value and not value.startswith("여기에") and value.strip())


def require_key(name: str) -> str:
    """필수 API 키가 없으면 친절한 오류를 발생시킵니다."""
    # 환경변수 값을 읽습니다.
    value = os.getenv(name)

    # 키가 없거나 예시 문자열이면 설정 방법을 안내하는 오류를 발생시킵니다.
    if not value or value.startswith("여기에"):
        raise RuntimeError(
            f"{name} 값이 .env에 없습니다. .env.example을 .env로 복사한 뒤 {name} 값을 입력하세요."
        )

    # 정상 키 값을 반환합니다.
    return value


def get_openai_client():
    """OpenAI 공식 SDK 클라이언트를 생성합니다."""
    # OpenAI 패키지는 API 실행 시점에만 import하여, 키 없이도 로컬 메뉴가 실행되게 합니다.
    from openai import OpenAI

    # OPENAI_API_KEY가 없으면 명확한 오류를 냅니다.
    api_key = require_key("OPENAI_API_KEY")

    # OpenAI 클라이언트 객체를 생성해서 반환합니다.
    return OpenAI(api_key=api_key)


def get_genai_client():
    """Google Gemini 공식 SDK 클라이언트를 생성합니다."""
    # google-genai 패키지는 API 실행 시점에만 import합니다.
    from google import genai

    # GOOGLE_API_KEY가 없으면 명확한 오류를 냅니다.
    api_key = require_key("GOOGLE_API_KEY")

    # Gemini 클라이언트 객체를 생성해서 반환합니다.
    return genai.Client(api_key=api_key)


def get_chat(provider: str = "openai", temperature: float = 0.0):
    """LangChain ChatModel을 provider 이름에 따라 생성합니다."""
    # provider가 openai이면 LangChain OpenAI ChatModel을 생성합니다.
    if provider == "openai":
        # OPENAI_API_KEY가 있는지 먼저 확인합니다.
        require_key("OPENAI_API_KEY")

        # LangChain용 OpenAI ChatModel 클래스를 import합니다.
        from langchain_openai import ChatOpenAI

        # 지정한 모델명과 temperature로 ChatOpenAI 객체를 반환합니다.
        return ChatOpenAI(model=OPENAI_CHAT_MODEL, temperature=temperature)

    # provider가 gemini이면 LangChain Gemini ChatModel을 생성합니다.
    if provider == "gemini":
        # GOOGLE_API_KEY가 있는지 먼저 확인합니다.
        require_key("GOOGLE_API_KEY")

        # LangChain용 Gemini ChatModel 클래스를 import합니다.
        from langchain_google_genai import ChatGoogleGenerativeAI

        # 지정한 Gemini 모델명과 temperature로 객체를 반환합니다.
        return ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=temperature)

    # 지원하지 않는 provider이면 오류를 발생시킵니다.
    raise ValueError(f"지원하지 않는 provider입니다: {provider}")


def print_env_status() -> None:
    """콘솔에서 API 키와 경로 상태를 확인할 때 사용하는 디버깅 함수입니다."""
    # 프로젝트 루트 경로를 출력합니다.
    print("ROOT:", ROOT)

    # data 폴더 경로와 존재 여부를 출력합니다.
    print("DATA:", DATA, "존재:", DATA.exists())

    # docs 폴더 경로와 존재 여부를 출력합니다.
    print("DOCS:", DOCS, "존재:", DOCS.exists())

    # OpenAI 키 설정 여부를 출력합니다.
    print("OPENAI_API_KEY 설정:", has_key("OPENAI_API_KEY"))

    # Gemini 키 설정 여부를 출력합니다.
    print("GOOGLE_API_KEY 설정:", has_key("GOOGLE_API_KEY"))

    # OpenAI 채팅 모델명을 출력합니다.
    print("OPENAI_CHAT_MODEL:", OPENAI_CHAT_MODEL)

    # Gemini 모델명을 출력합니다.
    print("GEMINI_MODEL:", GEMINI_MODEL)


# 이 파일을 직접 실행하면 환경 설정 상태를 확인합니다.
if __name__ == "__main__":
    print_env_status()
