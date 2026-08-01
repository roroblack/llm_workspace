# -*- coding: utf-8 -*-
"""
openai_agent_loop.py

OpenAI API의 tool calling을 수동 루프로 실행하는 예제입니다.
"""

# json은 OpenAI tool call 인자를 문자열에서 dict로 바꾸기 위해 사용합니다.
import json

# os는 환경변수에서 모델명을 읽기 위해 사용합니다.
import os

# OpenAI 공식 Python SDK 클라이언트를 가져옵니다.
from openai import OpenAI

# common.py의 require_key를 사용해 API 키 누락을 검사합니다.
from common import require_key

# 실습 도구 함수와 함수 매핑을 가져옵니다.
from data_tools import get_stock, get_reorder_level, TOOLS

# OpenAI 모델명은 .env의 OPENAI_MODEL을 우선 사용하고, 없으면 gpt-4o-mini를 사용합니다.
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# OpenAI에 전달할 도구 스키마 목록입니다.
OPENAI_TOOLS = [
    # 첫 번째 도구는 현재 재고 조회 함수입니다.
    {
        # OpenAI tool calling에서 함수형 도구임을 나타냅니다.
        "type": "function",
        # 함수 도구의 상세 정의입니다.
        "function": {
            # 모델이 호출할 함수 이름입니다.
            "name": "get_stock",
            # 모델이 도구를 고를 때 읽는 설명입니다.
            "description": "상품명 일부를 받아 현재 재고 수량을 조회한다. 재고 확인 질문에 사용한다.",
            # 함수 인자 JSON Schema입니다.
            "parameters": {
                # 인자는 JSON 객체 형태입니다.
                "type": "object",
                # product_name 인자 정의입니다.
                "properties": {
                    # 상품명 일부를 받는 문자열 필드입니다.
                    "product_name": {"type": "string", "description": "조회할 상품명 일부. 예: 스마트워치, 이어버드"}
                },
                # product_name은 필수 인자입니다.
                "required": ["product_name"],
            },
        },
    },
    # 두 번째 도구는 재주문 기준 조회 함수입니다.
    {
        # OpenAI tool calling에서 함수형 도구임을 나타냅니다.
        "type": "function",
        # 함수 도구의 상세 정의입니다.
        "function": {
            # 모델이 호출할 함수 이름입니다.
            "name": "get_reorder_level",
            # 모델이 도구를 고를 때 읽는 설명입니다.
            "description": "상품명 일부를 받아 재주문 기준 수량을 조회한다. 재주문 필요 여부 판단에 사용한다.",
            # 함수 인자 JSON Schema입니다.
            "parameters": {
                # 인자는 JSON 객체 형태입니다.
                "type": "object",
                # product_name 인자 정의입니다.
                "properties": {
                    # 상품명 일부를 받는 문자열 필드입니다.
                    "product_name": {"type": "string", "description": "조회할 상품명 일부. 예: 스마트워치, 이어버드"}
                },
                # product_name은 필수 인자입니다.
                "required": ["product_name"],
            },
        },
    },
]


def run_openai_agent(question: str, max_steps: int = 6) -> str | None:
    """OpenAI tool calling으로 ReAct 방식의 수동 Agent Loop를 실행합니다."""
    # OPENAI_API_KEY가 없으면 명확한 안내와 함께 종료합니다.
    api_key = require_key("OPENAI_API_KEY")
    # OpenAI 클라이언트를 생성합니다.
    client = OpenAI(api_key=api_key)
    # 시스템 메시지와 사용자 질문으로 대화 기록을 시작합니다.
    messages = [
        # 시스템 메시지는 에이전트 역할과 답변 언어를 고정합니다.
        {"role": "system", "content": "너는 승승장구몰 재고 관리 에이전트다. 도구로 재고와 재주문 기준을 확인하고 한국어로 답하라."},
        # 사용자 메시지는 실제 목표입니다.
        {"role": "user", "content": question},
    ]
    # 반복 호출 방지를 위해 이미 실행한 도구명+인자 조합을 저장합니다.
    seen_calls = set()
    # 최대 max_steps까지만 반복합니다.
    for step in range(1, max_steps + 1):
        # 현재 메시지 목록과 도구 목록을 모델에 전달합니다.
        response = client.chat.completions.create(
            # 사용할 OpenAI 모델입니다.
            model=OPENAI_MODEL,
            # 지금까지의 대화 기록입니다.
            messages=messages,
            # 모델이 사용할 수 있는 도구 스키마입니다.
            tools=OPENAI_TOOLS,
            # 도구 선택은 모델이 자동으로 판단하게 합니다.
            tool_choice="auto",
            # 일관된 도구 선택을 위해 temperature를 0으로 둡니다.
            temperature=0,
        )
        # 첫 번째 응답 메시지를 가져옵니다.
        message = response.choices[0].message
        # 토큰 사용량이 있으면 출력합니다.
        if response.usage:
            # 현재 호출의 토큰 사용량을 출력합니다.
            print(f"[STEP {step}] 입력 {response.usage.prompt_tokens} + 출력 {response.usage.completion_tokens} = 총 {response.usage.total_tokens} 토큰")
        # 도구 호출이 없으면 최종 답변으로 종료합니다.
        if not message.tool_calls:
            # 최종 답변 단계임을 출력합니다.
            print(f"[STEP {step}] 최종 답변")
            # 최종 답변 내용을 출력합니다.
            print(message.content)
            # 최종 답변을 반환합니다.
            return message.content
        # OpenAI 응답 메시지를 다음 호출을 위해 messages에 추가합니다.
        messages.append(message)
        # 모델이 요청한 도구 호출을 순회합니다.
        for call in message.tool_calls:
            # 호출한 함수 이름을 가져옵니다.
            name = call.function.name
            # 함수 인자 JSON 문자열을 dict로 변환합니다.
            args = json.loads(call.function.arguments or "{}")
            # 도구명과 정렬된 인자 튜플로 중복 감지용 서명을 만듭니다.
            signature = (name, tuple(sorted(args.items())))
            # 이미 같은 호출이 있었다면 중단합니다.
            if signature in seen_calls:
                # 반복 호출 경고를 출력합니다.
                print("[경고] 동일한 도구·인자 반복 호출 감지 → 강제 종료")
                # 안전 종료합니다.
                return None
            # 처음 보는 호출이면 기록합니다.
            seen_calls.add(signature)
            # 모델의 도구 호출 결정을 출력합니다.
            print(f"[STEP {step}] 호출: {name} {args}")
            # 실제 파이썬 함수를 실행합니다.
            result = TOOLS[name](**args)
            # 실행 결과를 출력합니다.
            print("           관찰:", result)
            # 도구 실행 결과를 OpenAI 메시지 형식으로 되돌립니다.
            messages.append({
                # tool 역할은 도구 실행 결과임을 의미합니다.
                "role": "tool",
                # 어떤 tool_call에 대한 결과인지 연결합니다.
                "tool_call_id": call.id,
                # 결과 문자열을 모델에 전달합니다.
                "content": result,
            })
        # 메시지가 너무 길어지면 시스템+첫 사용자+최근 메시지만 보존합니다.
        if len(messages) > 8:
            # 시스템 메시지와 첫 사용자 목표를 보존합니다.
            head = messages[:2]
            # 최근 6개 메시지를 보존합니다.
            tail = messages[-6:]
            # 보존할 메시지만 다시 합칩니다.
            messages = head + tail
    # 최대 스텝에 도달하면 안전장치 메시지를 출력합니다.
    print("[종료] 최대 스텝 도달 — 안전장치 작동")
    # 최종 답변이 없음을 의미합니다.
    return None


def run_openai_agent_demo() -> None:
    """OpenAI Agent Loop 데모를 실행합니다."""
    # API 키가 없거나 호출이 실패해도 프로그램 전체가 죽지 않도록 예외 처리합니다.
    try:
        # 대표 질문을 실행합니다.
        run_openai_agent("스마트워치 재고를 확인하고, 재주문이 필요하면 알려줘.")
    # SystemExit은 common.require_key가 키 누락 시 발생시킵니다.
    except SystemExit as e:
        # 키 설정 안내를 출력합니다.
        print(e)
    # 그 밖의 API 오류도 사용자에게 표시합니다.
    except Exception as e:
        # 예외 내용을 출력합니다.
        print("OpenAI 실행 오류:", e)
