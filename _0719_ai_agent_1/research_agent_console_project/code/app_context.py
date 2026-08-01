# -*- coding: utf-8 -*-
"""앱 전체에서 선택한 LLM 공급자를 공유하는 실행 컨텍스트 모듈입니다."""

# 사용자가 메뉴에서 선택한 공급자를 저장합니다.
# 기본값은 공통 모듈의 기본 공급자와 동일한 Gemini입니다.
_SELECTED_PROVIDER: str = "gemini"


def set_provider(provider: str) -> None:
    """OpenAI 또는 Gemini 중 사용자가 선택한 공급자를 저장합니다."""
    # 잘못된 문자열이 전달되면 뒤에서 알 수 없는 오류가 나므로 여기서 먼저 검사합니다.
    if provider not in {"openai", "gemini"}:
        # 허용되지 않은 값은 즉시 ValueError로 알립니다.
        raise ValueError("provider는 'openai' 또는 'gemini'만 사용할 수 있습니다.")

    # 모듈 전역 변수에 선택 값을 기록하기 위해 global 키워드를 사용합니다.
    global _SELECTED_PROVIDER
    # 검증을 통과한 공급자 이름을 저장합니다.
    _SELECTED_PROVIDER = provider


def get_provider() -> str:
    """현재 선택된 LLM 공급자 이름을 반환합니다."""
    # 다른 모듈이 common.get_chat(provider=...)에 전달할 수 있도록 문자열을 반환합니다.
    return _SELECTED_PROVIDER


def provider_label() -> str:
    """화면 출력용 한글 공급자 이름을 반환합니다."""
    # 내부 식별자가 openai이면 OpenAI를 표시하고, 나머지는 Gemini를 표시합니다.
    return "OpenAI" if _SELECTED_PROVIDER == "openai" else "Gemini"
