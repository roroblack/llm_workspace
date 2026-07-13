# -*- coding: utf-8 -*-
"""
llm_clients.py

역할:
    - common.py의 API 키 로딩 함수와 모델 상수를 사용합니다.
    - Gemini API와 OpenAI API로 직접 답변, CoT 답변, 자기검증을 실행합니다.
    - API 키가 없을 때 프로그램 전체가 중단되지 않도록 메뉴 단위로 예외를 처리합니다.
"""

# os는 .env에서 불러온 모델명 같은 환경변수를 읽기 위해 사용합니다.
import os

# re는 LLM 답변에서 마지막 숫자를 추출하기 위해 사용합니다.
import re

# common.py에서 Gemini 클라이언트 생성 함수와 모델명, 키 확인 함수를 가져옵니다.
from common import GEMINI_MODEL, get_genai_client, require_key


def extract_number(text: str) -> int | None:
    """LLM 답변 문자열에서 마지막 숫자를 정수로 추출합니다."""
    # 공백을 제거한 뒤 정규식으로 정수 형태의 숫자를 모두 찾습니다.
    nums = re.findall(r"-?\d[\d,]*", text.replace(" ", ""))

    # 숫자가 하나도 없으면 None을 반환하여 추출 실패를 표현합니다.
    if not nums:
        return None

    # 마지막 숫자에서 콤마를 제거하고 int로 변환합니다.
    return int(nums[-1].replace(",", ""))


def ask_gemini_direct(question: str) -> str:
    """Gemini API로 중간 설명 없이 최종 숫자만 요청합니다."""
    # google-genai의 설정 타입을 함수 내부에서 import하여, API 메뉴 실행 시점에만 필요하게 합니다.
    from google.genai import types

    # common.py의 get_genai_client()를 사용해 Gemini 클라이언트를 생성합니다.
    client = get_genai_client()

    # Gemini 모델에 직접 답변 프롬프트를 보냅니다.
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=f"{question}\n설명 없이 최종 숫자만 답하라.",
        config=types.GenerateContentConfig(temperature=0),
    )

    # 응답 텍스트를 반환합니다.
    return response.text.strip()


def ask_gemini_cot(question: str) -> str:
    """Gemini API로 단계적 풀이 후 마지막 줄에 정답을 요청합니다."""
    # google-genai 설정 타입을 가져옵니다.
    from google.genai import types

    # Gemini 클라이언트를 생성합니다.
    client = get_genai_client()

    # CoT 프롬프트를 사용해 단계적 풀이를 요청합니다.
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=(
            f"{question}\n"
            "단계적으로 풀어라. 각 계산을 한 줄씩 쓰고, "
            "맨 마지막 줄에 '정답: <숫자>' 형식으로 답하라."
        ),
        config=types.GenerateContentConfig(temperature=0),
    )

    # 응답 텍스트를 반환합니다.
    return response.text.strip()


def verify_gemini(question: str, cot_answer: str) -> str:
    """Gemini API로 CoT 풀이를 다시 검산합니다."""
    # google-genai 설정 타입을 가져옵니다.
    from google.genai import types

    # Gemini 클라이언트를 생성합니다.
    client = get_genai_client()

    # 문제와 1차 풀이를 함께 제공하여 검산을 요청합니다.
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=(
            f"[문제] {question}\n"
            f"[제출한 풀이]\n{cot_answer}\n\n"
            "위 풀이가 맞는지 다시 계산해 검산하라. "
            "틀렸다면 올바른 값을, 맞다면 그대로 '정답: <숫자>'로 확정하라."
        ),
        config=types.GenerateContentConfig(temperature=0),
    )

    # 검산 결과 텍스트를 반환합니다.
    return response.text.strip()


def get_openai_client():
    """common.py의 require_key()로 API 키를 확인한 뒤 OpenAI 클라이언트를 생성합니다."""
    # OpenAI 패키지는 OpenAI 메뉴를 실행할 때만 필요하므로 함수 내부에서 import합니다.
    from openai import OpenAI

    # OPENAI_API_KEY가 없으면 common.py의 안내 메시지와 함께 SystemExit이 발생합니다.
    api_key = require_key("OPENAI_API_KEY")

    # 확인된 API 키로 OpenAI 클라이언트를 생성합니다.
    return OpenAI(api_key=api_key)


def ask_openai_direct(question: str) -> str:
    """OpenAI API로 중간 설명 없이 최종 숫자만 요청합니다."""
    # OpenAI 클라이언트를 생성합니다.
    client = get_openai_client()

    # .env의 OPENAI_MODEL 값을 사용하고, 없으면 gpt-4o-mini를 기본값으로 사용합니다.
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # OpenAI Chat Completions API를 호출합니다.
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": "너는 계산 문제에 답하는 도우미다."},
            {"role": "user", "content": f"{question}\n설명 없이 최종 숫자만 답하라."},
        ],
    )

    # 첫 번째 선택지의 메시지 내용을 반환합니다.
    return response.choices[0].message.content.strip()


def ask_openai_cot(question: str) -> str:
    """OpenAI API로 단계적 풀이 후 마지막 줄에 정답을 요청합니다."""
    # OpenAI 클라이언트를 생성합니다.
    client = get_openai_client()

    # 사용할 OpenAI 모델명을 환경변수에서 가져옵니다.
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # 단계적 풀이를 요청하는 메시지를 보냅니다.
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": "너는 계산 과정을 정확히 작성하는 도우미다."},
            {
                "role": "user",
                "content": (
                    f"{question}\n"
                    "단계적으로 풀어라. 각 계산을 한 줄씩 쓰고, "
                    "맨 마지막 줄에 '정답: <숫자>' 형식으로 답하라."
                ),
            },
        ],
    )

    # 응답 텍스트를 반환합니다.
    return response.choices[0].message.content.strip()


def verify_openai(question: str, cot_answer: str) -> str:
    """OpenAI API로 CoT 풀이를 다시 검산합니다."""
    # OpenAI 클라이언트를 생성합니다.
    client = get_openai_client()

    # 사용할 모델명을 가져옵니다.
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # 문제와 기존 풀이를 함께 제공하여 검산을 요청합니다.
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": "너는 제출된 계산 풀이를 검산하는 도우미다."},
            {
                "role": "user",
                "content": (
                    f"[문제] {question}\n"
                    f"[제출한 풀이]\n{cot_answer}\n\n"
                    "위 풀이가 맞는지 다시 계산해 검산하라. "
                    "틀렸다면 올바른 값을, 맞다면 그대로 '정답: <숫자>'로 확정하라."
                ),
            },
        ],
    )

    # 검산 결과 텍스트를 반환합니다.
    return response.choices[0].message.content.strip()
