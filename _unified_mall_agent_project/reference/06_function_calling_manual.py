# -*- coding: utf-8 -*-
"""[복습 06] Function Calling — 자동 vs 수동 루프 (tool_choice 주의)

원본: function_calling_console_project/code/openai_app.py, gemini_app.py
공략집 스테이지 10

■ 핵심 원리
  "모델은 어떤 함수를 어떤 인자로 부를지 '결정'(JSON)만 하고, 실제 '실행'은 우리 코드가 한다."
  자동 FC(SDK가 실행까지) vs 수동 루프(우리가 제어) — 수동으로 원리를 배운다.

■ ★ tool_choice 주의 (실제로 통합에서 놓쳤던 디테일)
  - 공식 OpenAI API: tools가 있으면 tool_choice="auto"가 **기본값**이라 명시는 '필수는 아님'
    (명시하면 의도가 선명할 뿐).
  - 일부 OpenAI 호환 서버(llama-cpp function-calling 등): 호환성 때문에 tool_choice를
    **명시해야** 도구 호출이 켜지는 경우가 있다.
  → 그래서 "항상 tool_choice='auto' 명시"를 권장한다(OpenAI엔 무해, 호환서버엔 안전).
    통합 포팅 때 이걸 빠뜨려 로컬 서버에서 도구가 안 불렸고 나중에 버그로 잡았다.

■ 아래는 최소 happy-path 예제다. 실무 강건화(json.loads 실패, 알 수 없는 도구명,
  필수 인자 검증, 함수 예외 처리)는 통합의 app/agent/react.py 참조.

■ 수동 루프 4단계
  1) 모델 호출(tools 전달) → tool_calls(JSON) 반환
  2) 우리가 실제 함수 실행
  3) 실행 결과를 대화 기록에 되돌림 (OpenAI: role=tool / Gemini: function_response)
  4) 모델이 최종 자연어 답변을 낼 때까지 반복
"""

from __future__ import annotations

import json
import os

# --- 실제 실행할 도구(우리 코드) ---
PRICES = {"P0001": 79000, "P0002": 129000}


def get_price(product_code: str) -> int:
    return PRICES.get(product_code, -1)


TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_price",
        "description": "상품 코드로 가격을 조회한다",
        "parameters": {
            "type": "object",
            "properties": {"product_code": {"type": "string"}},
            "required": ["product_code"],
        },
    },
}]


def openai_manual_loop(question: str, max_steps: int = 3) -> str:
    """OpenAI 수동 tool-calling 루프."""
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    messages = [{"role": "user", "content": question}]

    for _ in range(max_steps):
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",  # OpenAI엔 기본값이라 무해, 호환서버 대비 명시(위 주의 참조)
        )
        msg = resp.choices[0].message
        messages.append(msg)  # 1) assistant(tool_calls) 먼저 기록

        if not msg.tool_calls:
            return msg.content  # 4) 최종 답변

        for tc in msg.tool_calls:  # 2) 우리가 실행
            args = json.loads(tc.function.arguments)
            result = get_price(**args)
            # 3) 결과를 role=tool 로 되돌림 (tool_call_id로 연결)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps({"price": result}),
            })
    return "[최대 단계 도달]"


# --- Gemini 수동 루프의 핵심 차이 (참조) ---
# Gemini는 결과를 types.Part.from_function_response(name=..., response={"result": ...})
# 형태로 history에 되돌린다(OpenAI의 role=tool 에 해당).

if __name__ == "__main__":
    print("도구 스키마:", TOOLS[0]["function"]["name"])
    print("직접 실행:", get_price("P0001"))  # 79000
    if os.environ.get("OPENAI_API_KEY"):
        print(openai_manual_loop("P0001 상품 가격 알려줘"))
    else:
        print("OPENAI_API_KEY 없음 — 수동 루프 구조만 복습(tool_choice='auto' 주의).")
