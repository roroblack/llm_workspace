# -*- coding: utf-8 -*-
"""제공된 common.py의 get_chat 함수를 통해 LLM 객체를 생성합니다."""
from app.core.common import get_chat

def create_chat_model(provider: str, temperature: float = 0.0):
    """Gemini 또는 OpenAI LangChain ChatModel을 반환합니다."""
    return get_chat(provider=provider, temperature=temperature)

def message_text(response) -> str:
    """LangChain 모델별 응답 차이를 문자열로 통일합니다."""
    content = getattr(response, "content", response)
    if isinstance(content, list):
        return "".join(str(item.get("text", item)) if isinstance(item, dict) else str(item) for item in content).strip()
    return str(content).strip()
