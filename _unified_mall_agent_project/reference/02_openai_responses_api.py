# -*- coding: utf-8 -*-
"""[복습 02] OpenAI Responses API — 신형 인터페이스

원본: openai_music_recommend_chatbot/app/services/openai_service.py
공략집 스테이지 6 (LLM API)

■ 통합 앱에서 증발한 것
  통합은 Chat Completions(OpenAI 호환)만 쓴다. OpenAI의 신형 Responses API
  (client.responses.create → output_text)는 통합 코드에 없다. 이 파일이 보존한다.

■ Chat Completions vs Responses API
  - Chat Completions: client.chat.completions.create(messages=[...]) → choices[0].message.content
  - Responses API:    client.responses.create(model, input=..., instructions=...) → resp.output_text
    · instructions(system 역할)와 input(사용자)이 분리돼 더 명확
    · reasoning 모델은 temperature/top_p 대신 reasoning={"effort": ...}
"""

from __future__ import annotations

import os

REASONING_PREFIXES = ("gpt-5", "o1", "o3", "o4")


def is_reasoning_model(model: str) -> bool:
    return (model or "").lower().startswith(REASONING_PREFIXES)


def ask(model: str, instructions: str, user_input: str,
        temperature: float | None = 0.7, max_output_tokens: int = 300) -> str:
    """Responses API 호출. OPENAI_API_KEY 필요."""
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    kwargs: dict = {
        "model": model,
        "instructions": instructions,   # system 지시(역할·규칙)
        "input": user_input,            # 사용자 입력
        "max_output_tokens": max_output_tokens,
    }
    if is_reasoning_model(model):
        # 추론 모델: temperature/top_p 대신 reasoning effort
        kwargs["reasoning"] = {"effort": "low"}
    elif temperature is not None:
        kwargs["temperature"] = temperature

    resp = client.responses.create(**kwargs)
    # output_text는 편의 속성이지만, 이것만 보면 '왜 비었는지'를 못 가린다.
    # 날것 복습이라면 status·incomplete_details·usage·output도 함께 관찰해야 정확하다:
    #   resp.status            # completed / incomplete
    #   resp.incomplete_details# 토큰 제한 등 미완 사유
    #   resp.usage             # 토큰 사용량(추론 토큰 포함 가능)
    #   resp.output            # tool call·refusal 등 여러 item일 수 있음
    # 특히 reasoning 모델은 max_output_tokens가 추론 토큰까지 포함해 빈 텍스트가 날 수 있다.
    return resp.output_text


if __name__ == "__main__":
    print("gpt-4o-mini reasoning?", is_reasoning_model("gpt-4o-mini"))  # False
    print("gpt-5 reasoning?      ", is_reasoning_model("gpt-5"))          # True
    if os.environ.get("OPENAI_API_KEY"):
        print(ask("gpt-4o-mini", "너는 친절한 뮤직 큐레이터다.", "잔잔한 밤에 들을 곡 추천해줘"))
