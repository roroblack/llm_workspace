# -*- coding: utf-8 -*-
"""LLM 응답 객체를 안전하게 문자열로 변환하는 공통 유틸리티 모듈입니다."""

from __future__ import annotations

from typing import Any


def extract_text(response: Any) -> str:
    """OpenAI/Gemini LangChain 응답에서 최종 문자열을 안전하게 추출합니다.

    LangChain 채팅 모델의 일반적인 반환값은 AIMessage이며 ``content`` 속성을 가집니다.
    다만 라이브러리 버전이나 테스트용 모의 객체에 따라 문자열, 리스트 또는 ``text`` 속성이
    전달될 수 있으므로 여러 형태를 순서대로 검사하여 호환성을 높입니다.
    """
    # 응답이 이미 문자열이면 별도 변환 없이 앞뒤 공백만 제거하여 반환합니다.
    if isinstance(response, str):
        return response.strip()

    # 일반적인 LangChain AIMessage 객체의 content 속성을 가져옵니다.
    content = getattr(response, "content", None)

    # content가 문자열이면 그대로 정리하여 반환합니다.
    if isinstance(content, str):
        return content.strip()

    # 일부 모델은 content를 텍스트 블록 리스트로 반환할 수 있으므로 리스트를 처리합니다.
    if isinstance(content, list):
        # 여러 블록에서 텍스트만 수집하기 위한 빈 리스트를 생성합니다.
        text_parts: list[str] = []

        # content 리스트 안의 블록을 하나씩 순회합니다.
        for block in content:
            # 블록이 딕셔너리이고 text 키가 있으면 해당 텍스트를 수집합니다.
            if isinstance(block, dict) and isinstance(block.get("text"), str):
                text_parts.append(block["text"])
            # 블록이 단순 문자열이면 해당 문자열을 그대로 수집합니다.
            elif isinstance(block, str):
                text_parts.append(block)

        # 수집한 텍스트 블록을 줄바꿈으로 합친 후 공백을 제거하여 반환합니다.
        if text_parts:
            return "\n".join(text_parts).strip()

    # 구형 또는 사용자 정의 객체가 text 속성을 제공하는 경우를 처리합니다.
    text = getattr(response, "text", None)

    # text 속성이 문자열이면 앞뒤 공백을 제거하여 반환합니다.
    if isinstance(text, str):
        return text.strip()

    # 마지막 수단으로 객체 전체를 문자열로 변환하여 빈 결과를 방지합니다.
    return str(response).strip()
