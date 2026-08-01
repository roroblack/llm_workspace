# -*- coding: utf-8 -*-
"""모든 콘솔 실습에서 함께 사용하는 공통 설정 모듈입니다."""

# 운영체제 환경변수를 읽기 위해 os 모듈을 가져옵니다.
import os
# 운영체제와 관계없이 경로를 안전하게 다루기 위해 pathlib 모듈을 가져옵니다.
import pathlib
# 프로젝트 루트의 .env 파일을 읽기 위해 load_dotenv 함수를 가져옵니다.
from dotenv import load_dotenv

# 현재 common.py 파일의 부모(code)의 부모를 프로젝트 최상위 폴더로 지정합니다.
ROOT = pathlib.Path(__file__).resolve().parent.parent
# 프로젝트의 실습 데이터가 저장될 data 폴더 경로를 생성합니다.
DATA = ROOT / "data"
# PDF 등 문서 파일이 저장될 data/docs 폴더 경로를 생성합니다.
DOCS = DATA / "docs"

# 프로젝트 루트에 있는 .env 파일의 환경변수를 현재 프로세스로 불러옵니다.
load_dotenv(ROOT / ".env")

# Gemini 채팅 모델명을 환경변수에서 읽고, 없으면 기본 모델명을 사용합니다.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
# Gemini 임베딩 모델명을 환경변수에서 읽고, 없으면 기본 모델명을 사용합니다.
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "models/gemini-embedding-001")
# OpenAI 채팅 모델명을 환경변수에서 읽고, 없으면 비교적 저비용 모델명을 사용합니다.
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def require_key(name: str) -> str:
    """필수 API 키가 없거나 예시 문자열이면 친절한 오류와 함께 실행을 종료합니다."""
    # 전달받은 이름에 해당하는 환경변수 값을 읽습니다.
    value = os.getenv(name)
    # 값이 비어 있거나 예시 문자열로 시작하면 실제 키가 입력되지 않은 것으로 판단합니다.
    if not value or value.startswith("여기에"):
        # 설정 방법을 보여 주는 SystemExit 예외를 발생시켜 현재 메뉴 실행만 중단합니다.
        raise SystemExit(
            f"[설정 필요] {name}가 .env 파일에 없습니다.\n"
            f"1) .env.example 파일을 .env 이름으로 복사합니다.\n"
            f"2) .env 파일에서 {name} 값을 실제 API 키로 변경합니다."
        )
    # 검증을 통과한 API 키 문자열을 호출한 쪽에 반환합니다.
    return value


def get_genai_client():
    """Google Gen AI의 원시 SDK 클라이언트를 생성하여 반환합니다."""
    # 함수가 실제 호출될 때만 google-genai 패키지를 가져와 선택적 의존성을 처리합니다.
    from google import genai
    # 검증된 Google API 키를 사용해 Gemini 클라이언트 객체를 생성합니다.
    return genai.Client(api_key=require_key("GOOGLE_API_KEY"))


def get_chat(provider: str = "gemini", temperature: float = 0.0):
    """provider 값에 맞는 LangChain 채팅 모델 객체를 생성하여 반환합니다."""
    # 사용자가 Gemini 공급자를 선택한 경우의 처리입니다.
    if provider == "gemini":
        # 모델 객체를 만들기 전에 Google API 키 존재 여부를 검증합니다.
        require_key("GOOGLE_API_KEY")
        # Gemini용 LangChain 채팅 모델 클래스를 지연 import합니다.
        from langchain_google_genai import ChatGoogleGenerativeAI
        # 공통 모델명과 temperature를 적용한 Gemini 채팅 객체를 반환합니다.
        return ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=temperature)
    # 사용자가 OpenAI 공급자를 선택한 경우의 처리입니다.
    if provider == "openai":
        # 모델 객체를 만들기 전에 OpenAI API 키 존재 여부를 검증합니다.
        require_key("OPENAI_API_KEY")
        # OpenAI용 LangChain 채팅 모델 클래스를 지연 import합니다.
        from langchain_openai import ChatOpenAI
        # 공통 모델명과 temperature를 적용한 OpenAI 채팅 객체를 반환합니다.
        return ChatOpenAI(model=OPENAI_MODEL, temperature=temperature)
    # 지원하지 않는 공급자 문자열이 들어오면 명확한 ValueError를 발생시킵니다.
    raise ValueError(f"알 수 없는 provider: {provider}")


def get_embeddings(provider: str = "gemini"):
    """provider 값에 맞는 LangChain 임베딩 객체를 생성하여 반환합니다."""
    # Gemini 임베딩을 선택한 경우의 처리입니다.
    if provider == "gemini":
        # Google API 키가 설정되어 있는지 먼저 검증합니다.
        require_key("GOOGLE_API_KEY")
        # Gemini 임베딩 클래스를 실제 사용 시점에 가져옵니다.
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        # 저장 공간과 실습 속도를 고려해 출력 차원을 768로 제한한 객체를 반환합니다.
        return GoogleGenerativeAIEmbeddings(model=GEMINI_EMBED_MODEL, output_dimensionality=768)
    # OpenAI 임베딩을 선택한 경우의 처리입니다.
    if provider == "openai":
        # OpenAI API 키가 설정되어 있는지 먼저 검증합니다.
        require_key("OPENAI_API_KEY")
        # OpenAI 임베딩 클래스를 실제 사용 시점에 가져옵니다.
        from langchain_openai import OpenAIEmbeddings
        # 비용과 성능 균형이 좋은 text-embedding-3-small 모델 객체를 반환합니다.
        return OpenAIEmbeddings(model="text-embedding-3-small")
    # 지원하지 않는 공급자 문자열이면 오류를 발생시킵니다.
    raise ValueError(f"알 수 없는 provider: {provider}")


# 이 파일을 직접 실행했을 때만 아래 진단 정보를 출력합니다.
if __name__ == "__main__":
    # 계산된 프로젝트 루트 경로를 출력합니다.
    print("ROOT:", ROOT)
    # data 폴더 경로와 실제 존재 여부를 출력합니다.
    print("DATA:", DATA, "(존재:", DATA.exists(), ")")
    # 현재 선택된 Gemini 모델명을 출력합니다.
    print("GEMINI_MODEL:", GEMINI_MODEL)
    # API 키의 실제 값은 노출하지 않고 설정 여부만 True/False로 출력합니다.
    print("키 설정 상태 - GOOGLE_API_KEY:", bool(os.getenv("GOOGLE_API_KEY")),
          "/ OPENAI_API_KEY:", bool(os.getenv("OPENAI_API_KEY")))
