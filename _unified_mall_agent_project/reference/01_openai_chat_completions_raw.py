# -*- coding: utf-8 -*-
"""[복습 01] OpenAI Chat Completions API — 날것 (gpt-5/o 계열 파라미터 분기)

원본: chatgpt_chatbot_project/app/services/openai_service.py
공략집 스테이지 6·7 (LLM API / 파라미터)

■ 통합 앱에서 증발한 것
  app/core/llm_clients.py 는 `OpenAI(api_key=...)` 한 줄로 감싸고, 호출도 단순
  `client.chat.completions.create(model, messages, temperature=0)` 뿐이다.
  아래의 "모델 계열별 파라미터 차이" 처리가 전부 사라진다. 이 파일이 그 지식을 보존한다.

■ 핵심 학습 포인트 (gpt-5 / o1·o3·o4 계열의 함정)
  1) gpt-5/o 계열은 temperature/top_p 커스텀 값을 지원하지 않는다 → 넣으면 400 오류
  2) 최대 토큰 파라미터명 변화: 예전 `max_tokens`는 **deprecated**이고 현재 권장은
     `max_completion_tokens`(가시 출력+추론 토큰 포함). o 계열은 max_tokens와 호환 안 됨.
     → 이 예제는 "레거시 max_tokens vs 현재 max_completion_tokens"의 차이를 보존한다.
  3) gpt-5/o는 답변 전에 "추론 토큰"을 먼저 소비 → 예산이 작으면 content가 빈다
     (finish_reason == "length"). 관찰 포인트: finish_reason·usage·빈 content.
  4) reasoning_effort 는 추론 계열에만 적용
  5) top_k 는 Chat Completions API가 아예 지원 안 함(실습 UI에서만 받고 호출엔 미포함)

⚠️ 주의(정확성): 아래 판별은 **이 예제가 명시적으로 지원하는 모델 목록** 기준의 단순화다.
   실무에선 모델명 prefix가 아니라 모델별 capability 테이블로 관리해야 한다(모델마다
   지원 endpoint·effort 값·temperature 지원 조건이 다르다). REASONING_MIN_TOKENS도
   공식 최소값이 아니라 '빈 응답 방지용 프로젝트 휴리스틱'이다.
"""

from __future__ import annotations

import os

# 프로젝트 휴리스틱(공식 최소값 아님): 추론 모델에 이보다 작은 예산을 주면 답변이 빌 수 있어
# 최소 이 값으로 상향해 finish_reason='length' 빈 응답을 예방한다.
REASONING_MIN_TOKENS = 2000

# 이 예제가 '추론 계열'로 취급하는 모델(단순화). 실무는 capability 테이블 권장.
_REASONING_PREFIXES = ("gpt-5", "o1", "o3", "o4")


def is_reasoning_model(model: str) -> bool:
    """(예제 단순화) 지정 prefix면 추론 계열로 간주. 실무는 capability로 판별."""
    return (model or "").lower().startswith(_REASONING_PREFIXES)


def build_params(model: str, messages: list[dict], *, temperature=None, top_p=None,
                 max_output_tokens=None, reasoning_effort=None) -> dict:
    """모델 계열에 맞춰 Chat Completions 파라미터를 안전하게 구성한다(핵심)."""
    params: dict = {"model": model, "messages": messages}
    restricted = is_reasoning_model(model)

    # 1) temperature/top_p 는 지원 모델에만
    if temperature is not None and not restricted:
        params["temperature"] = temperature
    if top_p is not None and not restricted:
        params["top_p"] = top_p

    # 2)·3) 최대 토큰: max_tokens는 deprecated, 현재 권장은 max_completion_tokens.
    #   이 예제는 레거시(max_tokens) vs 현재(max_completion_tokens) 차이를 대비해 보여준다.
    #   추론 모델은 사고 토큰까지 포함하므로 최소 예산으로 상향(프로젝트 휴리스틱).
    if max_output_tokens is not None:
        if restricted:
            params["max_completion_tokens"] = max(max_output_tokens, REASONING_MIN_TOKENS)
        else:
            params["max_tokens"] = max_output_tokens  # (레거시) 현행 코드는 max_completion_tokens 권장

    # 4) reasoning_effort 는 추론 계열에만
    if reasoning_effort is not None and restricted:
        params["reasoning_effort"] = reasoning_effort

    # 5) top_k 는 Chat Completions 미지원 → 넣지 않는다
    return params


def chat(model: str, user_message: str, **kwargs) -> str:
    """실제 호출. OPENAI_API_KEY 필요. finish_reason='length' 빈 응답도 처리."""
    from openai import OpenAI  # 지연 import (읽기 복습만 할 땐 불필요)

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])  # 키 없으면 KeyError로 명시 실패
    messages = [{"role": "user", "content": user_message}]
    params = build_params(model, messages, **kwargs)

    completion = client.chat.completions.create(**params)
    choice = completion.choices[0]
    reply, finish = choice.message.content, choice.finish_reason

    if not reply and finish == "length":
        # 추론 토큰이 예산을 소진해 답변이 비었다 → max_output_tokens를 키워 재호출해야 한다
        return "[빈 응답] 토큰 예산 부족(finish_reason=length). gpt-5/o는 추론 토큰을 먼저 소비함."
    return reply or ""


if __name__ == "__main__":
    # 파라미터 구성 로직은 키 없이도 확인 가능(복습 핵심)
    print("gpt-4o-mini:", build_params("gpt-4o-mini", [], temperature=0.7, max_output_tokens=100))
    print("gpt-5:      ", build_params("gpt-5", [], temperature=0.7, max_output_tokens=100, reasoning_effort="low"))
    # → gpt-4o-mini는 temperature+max_tokens, gpt-5는 temperature 제외+max_completion_tokens(2000 상향)+reasoning_effort
    if os.environ.get("OPENAI_API_KEY"):
        print(chat("gpt-4o-mini", "한 문장으로 자기소개 해줘", temperature=0.7, max_output_tokens=60))
