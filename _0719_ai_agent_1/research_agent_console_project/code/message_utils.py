# -*- coding: utf-8 -*-
"""OpenAI와 Gemini의 응답 객체 차이를 안전하게 처리하는 공통 함수입니다."""

from typing import Any


def extract_text(message: Any) -> str:
    """LangChain 메시지나 일반 문자열에서 최종 텍스트를 추출합니다."""
    # 이미 문자열이면 추가 처리 없이 그대로 반환합니다.
    if isinstance(message, str):
        return message

    # 최신 LangChain 메시지는 일반적으로 content 속성에 본문을 보관합니다.
    content = getattr(message, "content", None)

    # content가 문자열이면 가장 흔한 응답 형식이므로 바로 반환합니다.
    if isinstance(content, str):
        return content

    # 일부 모델은 멀티모달 블록 목록을 content에 반환할 수 있습니다.
    if isinstance(content, list):
        # 텍스트 블록만 모아 최종 문자열로 합치기 위한 리스트입니다.
        text_parts: list[str] = []

        # content 목록의 각 블록을 순서대로 확인합니다.
        for block in content:
            # 사전 형태 블록이면 text 필드를 우선 읽습니다.
            if isinstance(block, dict) and isinstance(block.get("text"), str):
                text_parts.append(block["text"])
            # 문자열 블록이면 그대로 추가합니다.
            elif isinstance(block, str):
                text_parts.append(block)

        # 추출한 텍스트 블록을 줄바꿈으로 연결합니다.
        if text_parts:
            return "\n".join(text_parts)

    # 일부 LangChain 버전은 text 속성을 제공하므로 호환성을 위해 확인합니다.
    text = getattr(message, "text", None)

    # text 속성이 문자열이면 반환합니다.
    if isinstance(text, str):
        return text

    # 어떤 형식인지 알 수 없더라도 화면에 확인할 수 있도록 문자열로 변환합니다.
    return str(message)


def last_message_text(result: Any) -> str:
    """create_agent.invoke 결과에서 마지막 AI 메시지 본문을 반환합니다."""
    # create_agent 결과는 보통 messages 키를 가진 사전 형태입니다.
    if isinstance(result, dict):
        # messages 목록을 안전하게 가져옵니다.
        messages = result.get("messages", [])

        # 메시지가 하나 이상 있으면 마지막 메시지가 최종 답변입니다.
        if messages:
            return extract_text(messages[-1])

    # 예상 형식이 아니면 전체 결과를 문자열로 바꾸어 디버깅 가능하게 반환합니다.
    return extract_text(result)
