# -*- coding: utf-8 -*-
"""콘솔 앱 전체에서 현재 선택한 LLM 공급자를 공유하는 상태 모듈입니다."""

# 사용자가 메뉴에서 선택한 공급자를 문자열로 보관합니다.
# common.py의 get_chat(provider=...) 함수가 요구하는 값과 동일하게 맞춥니다.
_PROVIDER: str = "gemini"


def set_provider(provider: str) -> None:
    """OpenAI 또는 Gemini 중 현재 사용할 공급자를 저장합니다."""
    global _PROVIDER
    # 오타나 잘못된 값이 이후 LLM 호출까지 전달되지 않도록 허용값을 검사합니다.
    if provider not in {"openai", "gemini"}:
        raise ValueError("provider는 'openai' 또는 'gemini'여야 합니다.")
    _PROVIDER = provider


def get_provider() -> str:
    """현재 선택된 LLM 공급자 이름을 반환합니다."""
    return _PROVIDER
