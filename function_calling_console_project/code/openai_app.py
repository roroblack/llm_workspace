# -*- coding: utf-8 -*-
"""OpenAI API의 도구 호출(tool calling) 수동 루프 예제 모듈입니다."""

# json은 OpenAI가 반환한 tool_call 인자를 파이썬 dict로 변환하기 위해 사용합니다.
import json

# os는 .env에 설정한 OPENAI_MODEL 값을 읽기 위해 사용합니다.
import os

# OpenAI SDK 클라이언트를 사용합니다.
from openai import OpenAI

# common.py의 require_key로 API 키 존재 여부를 확인합니다.
from common import require_key

# 도구로 사용할 파이썬 함수를 가져옵니다.
from tools import get_exchange_rate, get_stock

# OpenAI 모델명을 .env에서 읽고, 없으면 gpt-4o-mini를 기본값으로 사용합니다.
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# OpenAI tool schema는 모델에게 함수 이름, 설명, 입력 파라미터 구조를 알려 줍니다.
OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_stock",
            "description": "상품명 일부 또는 전체 이름을 받아 현재 재고 수량, 창고, 가격을 반환한다.",
            "parameters": {
                "type": "object",
                "properties": {"product_name": {"type": "string", "description": "조회할 상품명 또는 상품명 일부"}},
                "required": ["product_name"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_exchange_rate",
            "description": "통화 코드(USD, EUR, JPY, CNY)를 받아 1단위당 원화 환율을 반환한다.",
            "parameters": {
                "type": "object",
                "properties": {"currency": {"type": "string", "description": "USD, EUR, JPY, CNY 중 하나의 통화 코드"}},
                "required": ["currency"],
                "additionalProperties": False,
            },
        },
    },
]

# OpenAI가 반환한 함수 이름을 실제 파이썬 함수에 연결합니다.
TOOLS = {"get_stock": get_stock, "get_exchange_rate": get_exchange_rate}


def openai_manual_tool_calling() -> None:
    """OpenAI API로 모델의 도구 호출 결정과 실제 함수 실행 루프를 확인합니다."""
    # OPENAI_API_KEY가 없으면 명확한 안내와 함께 종료합니다.
    require_key("OPENAI_API_KEY")
    # OpenAI 클라이언트를 생성합니다.
    client = OpenAI()
    # 사용자 질문을 준비합니다.
    question = "이어버드 재고 있어? 그리고 USD 환율도 알려줘."
    # OpenAI Chat Completions API에 도구 목록과 질문을 전달합니다.
    first = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": question}],
        tools=OPENAI_TOOLS,
        tool_choice="auto",
        temperature=0,
    )
    # 첫 번째 응답 메시지를 가져옵니다.
    message = first.choices[0].message
    # 도구 호출이 없으면 일반 답변을 출력합니다.
    if not message.tool_calls:
        print(message.content)
        return
    # 최종 답변 생성을 위해 기존 대화 기록을 구성합니다.
    messages = [{"role": "user", "content": question}, message]
    # 모델이 요청한 도구 호출을 하나씩 실행합니다.
    for tool_call in message.tool_calls:
        # 함수 이름을 가져옵니다.
        name = tool_call.function.name
        # JSON 문자열 인자를 파이썬 dict로 변환합니다.
        args = json.loads(tool_call.function.arguments)
        # 모델의 결정을 출력합니다.
        print(f"모델의 결정 → 함수: {name} | 인자: {args}")
        # 실제 파이썬 함수를 실행합니다.
        result = TOOLS[name](**args)
        # 실행 결과를 출력합니다.
        print(f"우리가 실행한 결과: {result}")
        # 도구 결과를 OpenAI 메시지 형식으로 추가합니다.
        messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
    # 도구 결과까지 포함해 모델에 다시 보내 최종 자연어 답변을 생성합니다.
    final = client.chat.completions.create(model=OPENAI_MODEL, messages=messages, temperature=0.3)
    # 최종 답변을 출력합니다.
    print("\n[OpenAI Tool Calling 최종 답변]")
    print(final.choices[0].message.content)
