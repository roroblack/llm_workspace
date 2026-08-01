# -*- coding: utf-8 -*-
"""
common.py — 모든 실습에서 공통으로 사용하는 설정 모듈입니다.

주요 역할
1. 프로젝트 루트의 .env 파일을 읽습니다.
2. Gemini 또는 OpenAI용 LangChain 채팅 모델을 생성합니다.
3. 실습 데이터 폴더 경로를 한 곳에서 관리합니다.
4. API 키가 비어 있을 때 이해하기 쉬운 오류 메시지를 출력합니다.
"""

# 운영체제 환경변수를 읽기 위해 os 모듈을 가져옵니다.
import os

# 운영체제와 관계없이 파일 경로를 안전하게 처리하기 위해 pathlib을 가져옵니다.
import pathlib

# .env 파일의 환경변수를 현재 파이썬 프로세스에 로드하기 위해 load_dotenv를 가져옵니다.
from dotenv import load_dotenv


# 현재 common.py 파일은 프로젝트루트/code/common.py 위치에 있으므로 parent.parent가 프로젝트 루트입니다.
ROOT = pathlib.Path(__file__).resolve().parent.parent

# CSV 같은 실습 데이터를 저장하는 data 폴더 경로를 정의합니다.
DATA = ROOT / "data"

# 문서 기반 실습에서 사용할 수 있도록 data/docs 폴더 경로도 함께 정의합니다.
DOCS = DATA / "docs"

# 프로젝트 루트의 .env 파일을 읽어 API 키와 모델 설정을 환경변수에 등록합니다.
load_dotenv(ROOT / ".env")

# .env에 GEMINI_MODEL이 없으면 비교적 가벼운 기본 모델명을 사용합니다.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# .env에 OPENAI_MODEL이 없으면 교육용으로 비용이 비교적 낮은 기본 모델명을 사용합니다.
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Gemini 임베딩 실습에서 사용할 모델명을 환경변수 또는 기본값으로 읽습니다.
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "models/gemini-embedding-001")

# OpenAI 임베딩 실습에서 사용할 모델명을 환경변수 또는 기본값으로 읽습니다.
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")


def require_key(name: str) -> str:
    """지정한 API 키가 없거나 예시 문자열이면 프로그램을 안전하게 종료합니다."""

    # 환경변수 이름으로 실제 저장된 값을 읽습니다.
    value = os.getenv(name)

    # 값이 없거나 예시 문구로 시작하면 아직 실제 키가 입력되지 않은 상태입니다.
    if not value or value.startswith("여기에"):
        # 사용자가 바로 조치할 수 있도록 설정 순서를 포함한 종료 메시지를 발생시킵니다.
        raise SystemExit(
            f"[설정 필요] {name} 값이 .env 파일에 없습니다.\n"
            f"1) 프로젝트 루트의 .env.example 파일을 .env로 복사합니다.\n"
            f"2) .env 파일을 열어 {name}에 실제 API 키를 입력합니다."
        )

    # 검증을 통과한 실제 API 키 문자열을 호출한 함수에 반환합니다.
    return value


def get_genai_client():
    """Google의 공식 google-genai SDK 클라이언트를 생성하여 반환합니다."""

    # google-genai 패키지에서 genai 모듈을 함수 실행 시점에 가져옵니다.
    from google import genai

    # 검증된 Google API 키를 사용해 Gemini API 클라이언트를 생성합니다.
    return genai.Client(api_key=require_key("GOOGLE_API_KEY"))


def get_chat(provider: str = "gemini", temperature: float = 0.0):
    """provider 값에 따라 Gemini 또는 OpenAI LangChain ChatModel을 반환합니다."""

    # 사용자가 대소문자를 섞어 입력해도 처리하도록 공급자명을 소문자로 정규화합니다.
    normalized_provider = provider.strip().lower()

    # Gemini가 선택된 경우 Google용 LangChain 통합 모델을 생성합니다.
    if normalized_provider == "gemini":
        # 모델을 만들기 전에 Google API 키가 정상인지 검증합니다.
        require_key("GOOGLE_API_KEY")

        # Gemini용 LangChain 채팅 모델 클래스를 가져옵니다.
        from langchain_google_genai import ChatGoogleGenerativeAI

        # .env에서 읽은 모델명과 호출자가 지정한 temperature로 모델 객체를 반환합니다.
        return ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=temperature)

    # OpenAI가 선택된 경우 OpenAI용 LangChain 통합 모델을 생성합니다.
    if normalized_provider == "openai":
        # 모델을 만들기 전에 OpenAI API 키가 정상인지 검증합니다.
        require_key("OPENAI_API_KEY")

        # OpenAI용 LangChain 채팅 모델 클래스를 가져옵니다.
        from langchain_openai import ChatOpenAI

        # .env에서 읽은 모델명과 호출자가 지정한 temperature로 모델 객체를 반환합니다.
        return ChatOpenAI(model=OPENAI_MODEL, temperature=temperature)

    # 지원하지 않는 공급자 이름은 조용히 무시하지 않고 명확한 예외로 알립니다.
    raise ValueError(f"알 수 없는 provider입니다: {provider} (허용값: gemini, openai)")


def get_embeddings(provider: str = "gemini"):
    """provider 값에 따라 Gemini 또는 OpenAI 임베딩 모델을 반환합니다."""

    # 입력된 공급자 이름을 비교하기 쉬운 소문자로 변환합니다.
    normalized_provider = provider.strip().lower()

    # Gemini 임베딩 모델이 선택된 경우의 처리입니다.
    if normalized_provider == "gemini":
        # Google API 키가 설정되어 있는지 먼저 검사합니다.
        require_key("GOOGLE_API_KEY")

        # Gemini 임베딩용 LangChain 클래스를 가져옵니다.
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        # 저장 공간과 실습 속도를 고려하여 출력 차원을 768로 고정한 모델을 반환합니다.
        return GoogleGenerativeAIEmbeddings(
            model=GEMINI_EMBED_MODEL,
            output_dimensionality=768,
        )

    # OpenAI 임베딩 모델이 선택된 경우의 처리입니다.
    if normalized_provider == "openai":
        # OpenAI API 키가 설정되어 있는지 먼저 검사합니다.
        require_key("OPENAI_API_KEY")

        # OpenAI 임베딩용 LangChain 클래스를 가져옵니다.
        from langchain_openai import OpenAIEmbeddings

        # .env에서 지정한 OpenAI 임베딩 모델 객체를 생성하여 반환합니다.
        return OpenAIEmbeddings(model=OPENAI_EMBED_MODEL)

    # 허용되지 않은 공급자 이름이면 즉시 오류를 발생시킵니다.
    raise ValueError(f"알 수 없는 provider입니다: {provider} (허용값: gemini, openai)")


def print_environment_status() -> None:
    """프로젝트 경로, 모델명, API 키 로드 여부를 키 원문 노출 없이 출력합니다."""

    # 프로젝트 루트의 절대 경로를 출력합니다.
    print("ROOT               :", ROOT)

    # 데이터 폴더 경로와 실제 존재 여부를 함께 출력합니다.
    print("DATA               :", DATA, "(존재:", DATA.exists(), ")")

    # 현재 선택될 Gemini 모델명을 출력합니다.
    print("GEMINI_MODEL       :", GEMINI_MODEL)

    # 현재 선택될 OpenAI 모델명을 출력합니다.
    print("OPENAI_MODEL       :", OPENAI_MODEL)

    # 실제 키 문자열은 노출하지 않고 설정 여부만 True 또는 False로 출력합니다.
    print(
        "API 키 로드 상태    :",
        "GOOGLE_API_KEY=",
        bool(os.getenv("GOOGLE_API_KEY")),
        "/ OPENAI_API_KEY=",
        bool(os.getenv("OPENAI_API_KEY")),
    )


# common.py 파일을 직접 실행했을 때만 환경 점검 정보를 출력합니다.
if __name__ == "__main__":
    # 다른 모듈에서 import할 때는 실행되지 않고 직접 실행할 때만 호출됩니다.
    print_environment_status()
