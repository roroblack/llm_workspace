# -*- coding: utf-8 -*-
"""Gemini와 OpenAI 호출 기능을 모아 둔 서비스 파일입니다."""

# OpenAI API Key 확인을 위해 os 모듈을 불러옵니다.
import os

# 타입 힌트를 위해 Optional을 불러옵니다.
from typing import Optional

# 공통 Gemini 클라이언트 생성 함수와 모델명을 불러옵니다.
from app.common import get_genai_client, GEMINI_MODEL


def _safe_usage(resp) -> dict:
    """Gemini 응답 객체에서 토큰 사용량을 안전하게 꺼냅니다."""

    # usage_metadata가 없는 경우 None으로 처리하기 위해 getattr을 사용합니다.
    usage = getattr(resp, "usage_metadata", None)

    # usage_metadata가 없으면 모든 토큰 값을 None으로 반환합니다.
    if usage is None:
        return {
            "prompt_token_count": None,
            "candidates_token_count": None,
            "total_token_count": None,
        }

    # 사용량 속성을 안전하게 읽어 딕셔너리로 반환합니다.
    return {
        "prompt_token_count": getattr(usage, "prompt_token_count", None),
        "candidates_token_count": getattr(usage, "candidates_token_count", None),
        "total_token_count": getattr(usage, "total_token_count", None),
    }


def gemini_basic_call(prompt: str, temperature: float = 0.7, max_output_tokens: Optional[int] = 300) -> dict:
    """시스템 지시 없이 Gemini를 1회 호출합니다."""

    # google-genai 설정 객체를 사용하기 위해 types를 불러옵니다.
    from google.genai import types

    # Gemini 클라이언트를 생성합니다.
    client = get_genai_client()

    # temperature와 max_output_tokens를 설정합니다.
    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )

    # Gemini 모델에 요청을 보냅니다.
    resp = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=config,
    )

    # 답변 텍스트와 토큰 정보를 합쳐 반환합니다.
    return {"text": resp.text, **_safe_usage(resp)}


def gemini_role_chat(system_instruction: str, user_message: str, temperature: float = 0.3, max_output_tokens: Optional[int] = 300) -> dict:
    """시스템 지시를 포함해 Gemini를 1회 호출합니다."""

    # google-genai 설정 객체를 사용하기 위해 types를 불러옵니다.
    from google.genai import types

    # Gemini 클라이언트를 생성합니다.
    client = get_genai_client()

    # 시스템 지시, temperature, 최대 출력 토큰을 설정합니다.
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )

    # Gemini 모델에 요청을 보냅니다.
    resp = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=user_message,
        config=config,
    )

    # 답변 텍스트와 토큰 정보를 합쳐 반환합니다.
    return {"text": resp.text, **_safe_usage(resp)}


def gemini_temperature_diversity(prompt: str, temperature: float = 1.0, repeat_count: int = 5) -> dict:
    """같은 질문을 여러 번 호출하여 temperature에 따른 답변 다양성을 측정합니다."""

    # 답변들을 저장할 리스트를 만듭니다.
    answers = []

    # repeat_count만큼 같은 질문을 반복 호출합니다.
    for _ in range(repeat_count):
        result = gemini_basic_call(
            prompt=prompt,
            temperature=temperature,
            max_output_tokens=200,
        )
        answers.append(result["text"].strip())

    # set으로 중복을 제거한 뒤 고유 답변 개수를 계산합니다.
    unique_count = len(set(answers))

    # 측정 결과를 반환합니다.
    return {
        "temperature": temperature,
        "repeat_count": repeat_count,
        "answers": answers,
        "unique_count": unique_count,
    }


def gemini_token_compare(korean_text: str, english_text: str) -> dict:
    """한국어 입력과 영어 입력의 토큰 사용량을 비교합니다."""

    # 한국어 문장을 temperature 0으로 호출합니다.
    korean_result = gemini_basic_call(
        prompt=korean_text,
        temperature=0.0,
        max_output_tokens=200,
    )

    # 영어 문장을 temperature 0으로 호출합니다.
    english_result = gemini_basic_call(
        prompt=english_text,
        temperature=0.0,
        max_output_tokens=200,
    )

    # 두 결과를 나란히 반환합니다.
    return {
        "korean": korean_result,
        "english": english_result,
    }

# ---------------------------------------------------------------------------
# OpenAI 호출 함수 (Gemini 4종과 1:1로 대응됩니다.)
# ---------------------------------------------------------------------------


def _openai_usage(resp) -> dict:
    """OpenAI 응답 객체에서 토큰 사용량을 안전하게 꺼냅니다."""

    # usage 속성이 없는 경우 None으로 처리하기 위해 getattr을 사용합니다.
    usage = getattr(resp, "usage", None)

    # usage가 없으면 모든 토큰 값을 None으로 반환합니다.
    if usage is None:
        return {
            "prompt_token_count": None,
            "candidates_token_count": None,
            "total_token_count": None,
        }

    # Gemini 응답과 동일한 키 이름으로 맞춰 딕셔너리로 반환합니다.
    return {
        "prompt_token_count": getattr(usage, "prompt_tokens", None),
        "candidates_token_count": getattr(usage, "completion_tokens", None),
        "total_token_count": getattr(usage, "total_tokens", None),
    }


def _openai_generate(messages: list, temperature: float, max_tokens: Optional[int]) -> dict:
    """OpenAI Chat Completions API를 1회 호출하는 공통 내부 함수입니다."""

    # OPENAI_API_KEY가 없으면 명확한 오류를 발생시킵니다.
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY가 .env 파일에 설정되어 있지 않습니다.")

    # 사용할 OpenAI 모델명을 환경변수에서 읽고, 없으면 기본값을 사용합니다.
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    # OpenAI 공식 SDK의 클라이언트를 불러옵니다.
    from openai import OpenAI

    # 환경변수의 OPENAI_API_KEY를 자동으로 읽어 클라이언트를 생성합니다.
    client = OpenAI()

    # OpenAI 모델에 메시지 목록을 보냅니다.
    resp = client.chat.completions.create(
        model=openai_model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    # 답변 텍스트와 토큰 정보를 합쳐 반환합니다.
    return {"text": resp.choices[0].message.content, **_openai_usage(resp)}


def openai_basic_call(prompt: str, temperature: float = 0.7, max_output_tokens: Optional[int] = 300) -> dict:
    """시스템 지시 없이 OpenAI를 1회 호출합니다. (gemini_basic_call과 대응)"""

    # 사용자 메시지 하나만 담아 호출합니다.
    return _openai_generate(
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_output_tokens,
    )


def openai_role_chat(system_instruction: str, user_message: str, temperature: float = 0.3, max_output_tokens: Optional[int] = 300) -> dict:
    """시스템 지시를 포함해 OpenAI를 1회 호출합니다. (gemini_role_chat과 대응)"""

    # 시스템 지시와 사용자 질문을 함께 담아 호출합니다.
    return _openai_generate(
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_message},
        ],
        temperature=temperature,
        max_tokens=max_output_tokens,
    )


def openai_temperature_diversity(prompt: str, temperature: float = 1.0, repeat_count: int = 5) -> dict:
    """같은 질문을 여러 번 호출하여 temperature에 따른 답변 다양성을 측정합니다. (gemini_temperature_diversity와 대응)"""

    # 답변들을 저장할 리스트를 만듭니다.
    answers = []

    # repeat_count만큼 같은 질문을 반복 호출합니다.
    for _ in range(repeat_count):
        result = openai_basic_call(
            prompt=prompt,
            temperature=temperature,
            max_output_tokens=200,
        )
        answers.append(result["text"].strip())

    # set으로 중복을 제거한 뒤 고유 답변 개수를 계산합니다.
    unique_count = len(set(answers))

    # 측정 결과를 반환합니다.
    return {
        "temperature": temperature,
        "repeat_count": repeat_count,
        "answers": answers,
        "unique_count": unique_count,
    }


def openai_token_compare(korean_text: str, english_text: str) -> dict:
    """한국어 입력과 영어 입력의 토큰 사용량을 비교합니다. (gemini_token_compare와 대응)"""

    # 한국어 문장을 temperature 0으로 호출합니다.
    korean_result = openai_basic_call(
        prompt=korean_text,
        temperature=0.0,
        max_output_tokens=200,
    )

    # 영어 문장을 temperature 0으로 호출합니다.
    english_result = openai_basic_call(
        prompt=english_text,
        temperature=0.0,
        max_output_tokens=200,
    )

    # 두 결과를 나란히 반환합니다.
    return {
        "korean": korean_result,
        "english": english_result,
    }
