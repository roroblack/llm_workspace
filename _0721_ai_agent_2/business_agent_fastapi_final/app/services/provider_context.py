# -*- coding: utf-8 -*-
"""요청마다 선택한 OpenAI 또는 Gemini 공급자를 안전하게 전달합니다."""

# 비동기 요청별로 독립된 값을 보관하기 위해 ContextVar를 가져옵니다.
from contextvars import ContextVar
# 기본 공급자 설정을 재사용하기 위해 settings 값을 가져옵니다.
from app.core.settings import DEFAULT_PROVIDER

# 현재 요청의 공급자를 저장하는 컨텍스트 변수를 생성합니다.
_provider_context: ContextVar[str] = ContextVar("provider", default=DEFAULT_PROVIDER)


def set_provider(provider: str) -> None:
    """현재 요청에서 사용할 LLM 공급자를 저장합니다."""
    # 입력값의 앞뒤 공백을 제거하고 소문자로 통일합니다.
    normalized = provider.strip().lower()
    # 지원하지 않는 값이 들어오면 즉시 명확한 오류를 발생시킵니다.
    if normalized not in {"openai", "gemini"}:
        raise ValueError("provider는 openai 또는 gemini여야 합니다.")
    # 검증된 공급자 값을 현재 비동기 요청 컨텍스트에 저장합니다.
    _provider_context.set(normalized)


def get_provider() -> str:
    """현재 요청에 저장된 LLM 공급자를 반환합니다."""
    # ContextVar에 저장된 현재 값을 읽어 반환합니다.
    return _provider_context.get()
