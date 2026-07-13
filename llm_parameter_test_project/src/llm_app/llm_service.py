# -*- coding: utf-8 -*-
"""Gemini와 OpenAI를 호출하고 파라미터 실습을 돕는 서비스 파일입니다."""

# 필수 API Key를 읽고 모델명을 참조하기 위해 config 모듈을 불러옵니다.
from . import config


def ask_gemini(
    prompt: str,
    temperature: float = 0.7,
    top_p: float = 0.9,
    max_output_tokens: int = 1024,
) -> str:
    """Gemini 모델에 프롬프트를 보내고 생성된 텍스트를 반환합니다."""

    # google-genai 라이브러리는 실제 호출 시점에만 필요하므로 함수 안에서 불러옵니다.
    from google import genai

    # 생성 파라미터를 담기 위한 타입 모듈을 불러옵니다.
    from google.genai import types

    # .env에 저장된 Gemini API Key를 확인하고 읽어옵니다.
    api_key = config.require_env("GOOGLE_API_KEY")

    # API Key로 Gemini 클라이언트를 생성합니다.
    client = genai.Client(api_key=api_key)

    # temperature / top_p / 최대 토큰 수 등 생성 파라미터를 구성합니다.
    generation_config = types.GenerateContentConfig(
        temperature=temperature,
        top_p=top_p,
        max_output_tokens=max_output_tokens,
    )

    # 설정한 모델과 파라미터로 텍스트 생성을 요청합니다.
    response = client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=prompt,
        config=generation_config,
    )

    # 응답 본문이 비어 있을 수 있으므로 안전하게 문자열로 변환해 반환합니다.
    return (response.text or "").strip()


def ask_openai(
    prompt: str,
    temperature: float = 0.7,
    top_p: float = 0.9,
    max_tokens: int = 1024,
) -> str:
    """OpenAI 모델에 프롬프트를 보내고 생성된 텍스트를 반환합니다."""

    # openai 라이브러리는 실제 호출 시점에만 필요하므로 함수 안에서 불러옵니다.
    from openai import OpenAI

    # .env에 저장된 OpenAI API Key를 확인하고 읽어옵니다.
    api_key = config.require_env("OPENAI_API_KEY")

    # API Key로 OpenAI 클라이언트를 생성합니다.
    client = OpenAI(api_key=api_key)

    # 채팅 형식으로 사용자 프롬프트를 전달하며 생성 파라미터를 함께 지정합니다.
    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
    )

    # 첫 번째 응답 메시지의 내용을 꺼내 안전하게 문자열로 반환합니다.
    return (response.choices[0].message.content or "").strip()
