# -*- coding: utf-8 -*-
"""OpenAI와 Gemini의 LangChain 응답에서 텍스트를 안전하게 추출합니다."""

from typing import Any


def extract_text(response: Any) -> str:
    """LangChain 응답 객체 또는 문자열을 사람이 읽을 문자열로 변환합니다."""
    # 이미 문자열이라면 별도 변환 없이 양끝 공백만 제거합니다.
    if isinstance(response, str):
        return response.strip()
    # LangChain AIMessage는 일반적으로 content 속성에 본문을 저장합니다.
    content = getattr(response, "content", response)
    # 대부분의 OpenAI/Gemini 응답은 content가 문자열이므로 바로 반환합니다.
    if isinstance(content, str):
        return content.strip()
    # 일부 모델은 텍스트 조각을 리스트 형태로 반환할 수 있어 조각별로 수집합니다.
    if isinstance(content, list):
        # 최종 텍스트를 담을 빈 리스트를 준비합니다.
        parts: list[str] = []
        # 응답 조각을 순서대로 확인합니다.
        for item in content:
            # 딕셔너리 조각이면 text 키 또는 content 키를 우선 찾습니다.
            if isinstance(item, dict):
                value = item.get("text") or item.get("content") or ""
                # 값이 존재하면 문자열로 바꾸어 결과 목록에 추가합니다.
                if value:
                    parts.append(str(value))
            else:
                # 딕셔너리가 아닌 조각은 일반 문자열로 변환합니다.
                parts.append(str(item))
        # 여러 조각을 줄바꿈으로 결합해 하나의 본문으로 반환합니다.
        return "\n".join(parts).strip()
    # 예상하지 못한 객체도 정보가 사라지지 않도록 문자열로 변환합니다.
    return str(content).strip()
