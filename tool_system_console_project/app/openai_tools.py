# -*- coding: utf-8 -*-
"""OpenAI API로 도구 선택과 Tool Calling을 실험하는 모듈입니다."""

from __future__ import annotations

# json은 OpenAI가 반환한 arguments 문자열을 dict로 변환하는 데 사용합니다.
import json

# OpenAI 공식 SDK 클라이언트입니다.
from openai import OpenAI

# common.py의 require_key는 .env에 API 키가 있는지 확인합니다.
from common import require_key

# 실제 실행할 파이썬 도구 함수 매핑을 가져옵니다.
from data_tools import TOOL_MAP


# OpenAI에 전달할 도구 스키마 목록입니다.
OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_price",
            "description": "상품명 일부를 받아 판매가 원화 가격을 반환한다. 가격/얼마 질문에 사용한다.",
            "parameters": {
                "type": "object",
                "properties": {"product_name": {"type": "string", "description": "상품명 또는 상품명 일부"}},
                "required": ["product_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock",
            "description": "상품명 일부를 받아 현재 재고 수량과 창고를 반환한다. 재고/품절 질문에 사용한다.",
            "parameters": {
                "type": "object",
                "properties": {"product_name": {"type": "string", "description": "상품명 또는 상품명 일부"}},
                "required": ["product_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "주문번호를 받아 주문 상품과 배송 상태를 반환한다. 주문/배송 추적 질문에 사용한다.",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string", "description": "주문번호 예: O000106"}},
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_product",
            "description": "카테고리 또는 키워드로 상품 후보 목록을 반환한다. 어떤 상품이 있는지 묻는 질문에 사용한다.",
            "parameters": {
                "type": "object",
                "properties": {"keyword": {"type": "string", "description": "상품명 일부 또는 카테고리 키워드"}},
                "required": ["keyword"],
            },
        },
    },
]


def get_openai_client() -> OpenAI:
    """OPENAI_API_KEY를 확인한 뒤 OpenAI 클라이언트를 생성합니다."""
    # require_key는 키가 없으면 사용자가 .env를 설정하도록 안내하고 종료합니다.
    api_key = require_key("OPENAI_API_KEY")
    # OpenAI 클라이언트를 생성하여 반환합니다.
    return OpenAI(api_key=api_key)


def run_openai_tool_choice_demo() -> None:
    """OpenAI 모델이 어떤 도구를 고르는지 확인합니다."""
    # OpenAI 클라이언트를 생성합니다.
    client = get_openai_client()
    # 실습 질문 목록을 준비합니다.
    questions = [
        "슬림핏 청바지 얼마야?",
        "이어버드 재고 있어?",
        "주문 O000106 배송 어디까지 왔어?",
        "패션의류 쪽에 어떤 상품들 있어?",
    ]
    # 질문마다 모델의 tool_calls를 확인합니다.
    for question in questions:
        # chat.completions.create는 OpenAI Chat Completions API 호출입니다.
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": question}],
            tools=OPENAI_TOOLS,
            tool_choice="auto",
            temperature=0,
        )
        # 첫 번째 응답 메시지를 가져옵니다.
        message = response.choices[0].message
        # tool_calls가 없으면 도구 미선택으로 출력합니다.
        if not message.tool_calls:
            print(f"'{question}' → 도구 미선택")
            continue
        # 선택된 도구 이름과 인자를 출력합니다.
        for call in message.tool_calls:
            print(f"'{question}' → {call.function.name}({call.function.arguments})")


def run_openai_tool_execution_demo() -> None:
    """OpenAI Tool Calling 요청을 실제 파이썬 함수로 실행하고 최종 답변을 생성합니다."""
    # OpenAI 클라이언트를 생성합니다.
    client = get_openai_client()
    # 사용자 질문을 준비합니다.
    question = "이어버드 재고와 슬림핏 청바지 가격을 알려줘."
    # 첫 번째 호출에서 모델이 필요한 도구를 고르게 합니다.
    first = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": question}],
        tools=OPENAI_TOOLS,
        tool_choice="auto",
        temperature=0,
    )
    # 모델 응답 메시지를 가져옵니다.
    assistant_message = first.choices[0].message
    # 대화 기록에 사용자 질문과 모델의 도구 호출 결정을 넣습니다.
    messages = [
        {"role": "user", "content": question},
        assistant_message,
    ]
    # 도구 호출이 없으면 일반 답변을 출력합니다.
    if not assistant_message.tool_calls:
        print(assistant_message.content)
        return
    # 각 도구 호출을 실제 파이썬 함수로 실행합니다.
    for call in assistant_message.tool_calls:
        # 함수 이름을 가져옵니다.
        name = call.function.name
        # arguments JSON 문자열을 dict로 변환합니다.
        args = json.loads(call.function.arguments)
        # TOOL_MAP에서 실제 파이썬 함수를 찾습니다.
        func = TOOL_MAP[name]
        # 인자를 풀어서 실제 함수를 실행합니다.
        result = func(**args)
        # 실행 결과를 OpenAI가 이해하는 tool 메시지로 대화 기록에 추가합니다.
        messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
    # 도구 실행 결과를 포함한 대화 기록으로 최종 답변을 요청합니다.
    final = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=OPENAI_TOOLS,
        temperature=0,
    )
    # 최종 답변을 출력합니다.
    print(final.choices[0].message.content)
