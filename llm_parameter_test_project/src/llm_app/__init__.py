# -*- coding: utf-8 -*-
"""llm_app 패키지를 초기화하고 주요 기능을 한곳에서 노출하는 파일입니다."""

# 설정 관련 함수와 상수를 패키지 최상위에서 바로 쓸 수 있게 불러옵니다.
from .config import (
    GEMINI_MODEL,
    OPENAI_MODEL,
    get_env_status,
    is_placeholder,
    require_env,
)

# LLM 호출 함수를 패키지 최상위에서 바로 쓸 수 있게 불러옵니다.
from .llm_service import ask_gemini, ask_openai

# 콘솔 입출력 보조 함수를 패키지 최상위에서 바로 쓸 수 있게 불러옵니다.
from .utils import ask_float, ask_int, print_header, print_result

# from llm_app import * 사용 시 외부에 공개할 이름 목록을 정의합니다.
__all__ = [
    "GEMINI_MODEL",
    "OPENAI_MODEL",
    "get_env_status",
    "is_placeholder",
    "require_env",
    "ask_gemini",
    "ask_openai",
    "ask_float",
    "ask_int",
    "print_header",
    "print_result",
]
