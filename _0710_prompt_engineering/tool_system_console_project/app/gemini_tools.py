# -*- coding: utf-8 -*-
"""Gemini API로 도구 선택과 자동 Function Calling을 실험하는 모듈입니다."""

from __future__ import annotations

# common.py에서 Gemini 클라이언트 생성 함수와 모델명을 가져옵니다.
from common import GEMINI_MODEL, get_genai_client

# google.genai.types는 Function Calling 설정 객체를 제공합니다.
from google.genai import types

# data_tools는 실습용 도구 함수 목록을 제공합니다.
from data_tools import (
    GEMINI_TOOLS,
    get_product_info_clear,
    get_stock,
    search_product_clear,
)


def which_tool(question: str, tools: list | None = None) -> None:
    """자동 실행을 끄고 Gemini가 어떤 도구를 선택하는지 관찰합니다."""
    # tools가 None이면 기본 도구 4개를 사용합니다.
    selected_tools = GEMINI_TOOLS if tools is None else tools
    # Gemini 클라이언트를 생성합니다.
    client = get_genai_client()
    # 모델을 호출하되 자동 함수 실행을 비활성화하여 선택 결과만 받습니다.
    resp = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=question,
        config=types.GenerateContentConfig(
            tools=selected_tools,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            temperature=0,
        ),
    )
    # function_calls가 없으면 모델이 도구를 선택하지 않았다는 뜻입니다.
    calls = resp.function_calls or []
    # 선택된 도구가 없으면 안내를 출력합니다.
    if not calls:
        print(f"'{question}' → 도구 미선택")
        return
    # 선택된 도구 이름과 인자를 출력합니다.
    for fc in calls:
        print(f"'{question}' → {fc.name}({dict(fc.args)})")


def ask_with_gemini(question: str) -> None:
    """Gemini 자동 Function Calling으로 도구 실행 결과가 반영된 최종 답변을 출력합니다."""
    # Gemini 클라이언트를 생성합니다.
    client = get_genai_client()
    # tools에 파이썬 함수를 넘기면 SDK가 자동으로 함수 호출과 결과 전달을 처리합니다.
    resp = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=question,
        config=types.GenerateContentConfig(tools=GEMINI_TOOLS, temperature=0),
    )
    # 최종 답변 텍스트를 출력합니다.
    print(resp.text)


def run_gemini_tool_choice_demo() -> None:
    """제6강 도구 4개 선택 관찰 예제를 실행합니다."""
    # 실습 질문 목록을 준비합니다.
    questions = [
        "슬림핏 청바지 얼마야?",
        "이어버드 재고 있어?",
        "주문 O000106 배송 어디까지 왔어?",
        "패션의류 쪽에 어떤 상품들 있어?",
    ]
    # 각 질문에 대해 선택 도구를 출력합니다.
    for question in questions:
        which_tool(question)


def run_similar_tool_demo() -> None:
    """비슷한 도구를 명확한 독스트링으로 구분하는 예제를 실행합니다."""
    # 비슷한 상품 조회 도구 두 개를 별도 목록으로 준비합니다.
    tools = [get_product_info_clear, search_product_clear]
    # 상품 ID 질문은 정확검색 도구가 선택되어야 합니다.
    which_tool("상품ID P0001 상세정보 알려줘.", tools)
    # 키워드 질문은 키워드검색 도구가 선택되어야 합니다.
    which_tool("이어버드 들어간 상품들 다 찾아줘.", tools)


def run_gemini_answer_demo() -> None:
    """Gemini 자동 도구 실행 결과를 확인합니다."""
    # 가격 조회 질문을 실행합니다.
    print("\nQ: 슬림핏 청바지 얼마야?")
    ask_with_gemini("슬림핏 청바지 얼마야?")
    # 재고 조회 질문을 실행합니다.
    print("\nQ: 이어버드 재고 있어?")
    ask_with_gemini("이어버드 재고 있어?")
