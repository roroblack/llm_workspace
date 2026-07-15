# -*- coding: utf-8 -*-
"""[복습 03] Gemini 날것 SDK — google-genai

원본: fastapi_llm_parameter_test_project/app/services/llm_service.py, common.py
공략집 스테이지 6 (LLM API)

■ 통합 앱에서 증발한 것
  통합은 로컬/OpenAI는 openai SDK, Gemini는 LangChain(ChatGoogleGenerativeAI)만 쓴다.
  Gemini 공식 SDK(google-genai)의 날것 호출 방식(generate_content, GenerateContentConfig,
  usage_metadata, 임베딩)은 통합 코드에 안 보인다. 이 파일이 보존한다.

■ 핵심
  - 클라이언트: genai.Client(api_key=...)
  - 텍스트: client.models.generate_content(model, contents, config=GenerateContentConfig(...))
    · system_instruction, temperature, top_p, max_output_tokens 를 config로 전달
  - 응답: resp.text (본문), resp.usage_metadata (토큰 수)
  - 임베딩: client.models.embed_content(model, contents)  (models/gemini-embedding-001)
"""

from __future__ import annotations

import os


def get_client():
    from google import genai

    return genai.Client(api_key=os.environ["GOOGLE_API_KEY"])


def generate(prompt: str, system: str | None = None, temperature: float = 0.7,
             max_output_tokens: int = 300) -> dict:
    """Gemini 텍스트 생성. 응답 본문 + 토큰 사용량을 함께 반환한다."""
    from google.genai import types

    client = get_client()
    config = types.GenerateContentConfig(
        system_instruction=system,     # 역할/규칙 (system 지시)
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=config,
    )
    usage = getattr(resp, "usage_metadata", None)
    return {
        "text": resp.text,
        # 토큰 감각: 입력/출력 토큰 수 (한국어가 영어보다 토큰을 더 씀을 관찰 가능)
        "input_tokens": getattr(usage, "prompt_token_count", None),
        "output_tokens": getattr(usage, "candidates_token_count", None),
    }


def embed(text: str) -> list[float]:
    """Gemini 임베딩(gemini-embedding-001). 통합은 로컬 ko-sroberta를 쓰므로 이건 참조용."""
    client = get_client()
    resp = client.models.embed_content(model="models/gemini-embedding-001", contents=text)
    return resp.embeddings[0].values


if __name__ == "__main__":
    if os.environ.get("GOOGLE_API_KEY"):
        out = generate("승승장구몰을 한 문장으로 홍보해줘", system="너는 마케터다.")
        print("text:", out["text"])
        print("tokens:", out["input_tokens"], "->", out["output_tokens"])
    else:
        print("GOOGLE_API_KEY 없음 — 코드 구조만 복습(generate/embed 시그니처 참조).")
