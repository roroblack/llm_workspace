# -*- coding: utf-8 -*-
"""실행 중 선택된 LLM 공급자를 보관하는 간단한 공용 상태 모듈입니다."""

# 앱이 처음 실행될 때 기본 공급자를 Gemini로 지정합니다.
_provider = "gemini"


def set_provider(provider: str) -> None:
    """사용자가 선택한 공급자 이름을 검증한 뒤 전역 상태에 저장합니다."""
    # 함수 안에서 모듈 전역 변수를 변경할 수 있도록 global 키워드를 선언합니다.
    global _provider
    # 전달된 문자열의 앞뒤 공백을 제거하고 소문자로 통일합니다.
    normalized = provider.strip().lower()
    # 지원하지 않는 공급자가 들어오면 잘못된 설정임을 즉시 알립니다.
    if normalized not in {"gemini", "openai"}:
        raise ValueError("provider는 'gemini' 또는 'openai'만 사용할 수 있습니다.")
    # 검증을 통과한 공급자 값을 전역 변수에 저장합니다.
    _provider = normalized


def get_provider() -> str:
    """현재 선택되어 있는 공급자 식별자를 반환합니다."""
    # 다른 모듈에서 get_chat과 get_embeddings에 전달할 값을 반환합니다.
    return _provider


def get_provider_label() -> str:
    """콘솔 화면에 출력할 공급자 한글 표시명을 반환합니다."""
    # 내부 식별자가 gemini이면 Google Gemini라는 표시명을 반환합니다.
    if _provider == "gemini":
        return "Google Gemini"
    # gemini가 아니면 검증상 openai이므로 OpenAI라는 표시명을 반환합니다.
    return "OpenAI"
