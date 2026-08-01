# -*- coding: utf-8 -*-
"""API 키, 모델 생성, 공통 경로를 관리하는 모듈입니다."""

# 운영체제 환경변수를 읽기 위해 os 모듈을 가져옵니다.
import os
# 파일과 폴더 경로를 운영체제에 독립적으로 처리하기 위해 Path를 가져옵니다.
from pathlib import Path
# .env 파일의 값을 환경변수로 등록하기 위해 load_dotenv를 가져옵니다.
from dotenv import load_dotenv

# 현재 파일(code/common.py)의 상위 상위 폴더를 프로젝트 루트로 지정합니다.
ROOT = Path(__file__).resolve().parent.parent
# 프로젝트의 실습 데이터 폴더 경로를 지정합니다.
DATA = ROOT / "data"
# 실행 결과를 저장할 폴더 경로를 지정합니다.
OUTPUTS = ROOT / "outputs"
# 프로젝트 루트의 .env 파일을 읽어 API 키와 모델 설정을 로드합니다.
load_dotenv(ROOT / ".env")

# 환경변수에 OpenAI 모델이 없으면 교육용 기본 모델명을 사용합니다.
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
# 환경변수에 Gemini 모델이 없으면 교육용 기본 모델명을 사용합니다.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

def require_key(name: str) -> str:
    """필수 API 키가 실제 값으로 설정되었는지 검사합니다."""
    # 지정한 이름의 환경변수 값을 읽습니다.
    value = os.getenv(name, "").strip()
    # 값이 없거나 예제 문구가 남아 있으면 명확한 설정 오류를 발생시킵니다.
    if not value or value.startswith("여기에"):
        raise RuntimeError(f"[설정 필요] .env 파일에 {name}의 실제 값을 입력하세요.")
    # 검증된 API 키 문자열을 호출한 위치에 반환합니다.
    return value

def get_chat(provider: str, temperature: float = 0.0):
    """선택한 provider에 맞는 LangChain 채팅 모델을 생성합니다."""
    # 사용자가 입력한 공급자 이름의 앞뒤 공백을 제거하고 소문자로 통일합니다.
    normalized = provider.strip().lower()
    # OpenAI가 선택되었는지 확인합니다.
    if normalized == "openai":
        # OpenAI API 키가 설정되었는지 먼저 검사합니다.
        require_key("OPENAI_API_KEY")
        # OpenAI 채팅 모델 클래스를 필요한 시점에만 가져옵니다.
        from langchain_openai import ChatOpenAI
        # .env의 모델명과 전달받은 temperature로 모델 객체를 반환합니다.
        return ChatOpenAI(model=OPENAI_MODEL, temperature=temperature)
    # Gemini가 선택되었는지 확인합니다.
    if normalized == "gemini":
        # Google API 키가 설정되었는지 먼저 검사합니다.
        require_key("GOOGLE_API_KEY")
        # Gemini 채팅 모델 클래스를 필요한 시점에만 가져옵니다.
        from langchain_google_genai import ChatGoogleGenerativeAI
        # .env의 모델명과 전달받은 temperature로 모델 객체를 반환합니다.
        return ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=temperature)
    # 지원하지 않는 공급자 이름이면 허용값을 포함한 오류를 발생시킵니다.
    raise ValueError("provider는 'openai' 또는 'gemini'여야 합니다.")

def print_environment_status() -> None:
    """프로젝트 경로, 데이터, API 키 설정 여부를 화면에 표시합니다."""
    # 프로젝트 루트 경로를 출력합니다.
    print(f"프로젝트 루트: {ROOT}")
    # 데이터 폴더의 존재 여부를 출력합니다.
    print(f"데이터 폴더: {DATA} / 존재={DATA.exists()}")
    # OpenAI 키는 실제 값을 노출하지 않고 설정 여부만 출력합니다.
    print(f"OPENAI_API_KEY 설정: {bool(os.getenv('OPENAI_API_KEY'))}")
    # Google 키도 실제 값을 노출하지 않고 설정 여부만 출력합니다.
    print(f"GOOGLE_API_KEY 설정: {bool(os.getenv('GOOGLE_API_KEY'))}")
    # 현재 사용할 OpenAI 모델명을 출력합니다.
    print(f"OPENAI_MODEL: {OPENAI_MODEL}")
    # 현재 사용할 Gemini 모델명을 출력합니다.
    print(f"GEMINI_MODEL: {GEMINI_MODEL}")
