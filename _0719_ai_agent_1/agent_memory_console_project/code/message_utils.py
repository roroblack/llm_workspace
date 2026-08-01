# -*- coding: utf-8 -*-
"""모델별 메시지 형식 차이를 안전하게 처리하는 공통 함수 모음입니다."""

# Any는 다양한 메시지 객체를 받을 수 있도록 사용하는 타입입니다.
from typing import Any


def message_to_text(message: Any) -> str:
    """OpenAI와 Gemini의 메시지 객체에서 최종 문자열만 안전하게 꺼냅니다."""
    # LangChain v1 메시지에 text 속성이 있으면 가장 먼저 사용합니다.
    text_value = getattr(message, "text", None)
    # text 속성이 문자열이고 내용이 있으면 그대로 반환합니다.
    if isinstance(text_value, str) and text_value.strip():
        return text_value.strip()

    # 일부 모델은 content 속성에 문자열 또는 콘텐츠 블록 목록을 넣습니다.
    content = getattr(message, "content", message)
    # content가 문자열이면 앞뒤 공백을 제거하여 반환합니다.
    if isinstance(content, str):
        return content.strip()

    # content가 리스트이면 각 블록에서 텍스트를 찾아 하나의 문자열로 합칩니다.
    if isinstance(content, list):
        # 추출된 텍스트 조각을 저장할 빈 리스트를 만듭니다.
        parts: list[str] = []
        # 콘텐츠 블록을 하나씩 순회합니다.
        for block in content:
            # 블록이 문자열이면 그대로 결과 목록에 추가합니다.
            if isinstance(block, str):
                parts.append(block)
            # 블록이 딕셔너리이면 text 또는 content 키를 확인합니다.
            elif isinstance(block, dict):
                # text 키를 우선하고 없으면 content 키를 사용합니다.
                value = block.get("text") or block.get("content")
                # 찾은 값이 문자열일 때만 결과 목록에 추가합니다.
                if isinstance(value, str):
                    parts.append(value)
        # 추출된 문자열 조각을 줄바꿈으로 합쳐 반환합니다.
        return "\n".join(parts).strip()

    # 알려지지 않은 형식은 str로 변환하여 프로그램이 중단되지 않게 합니다.
    return str(content).strip()
