# -*- coding: utf-8 -*-
"""
Gemini API 기반 보조 응답 서비스입니다.

이 프로젝트의 핵심 ReAct 루프는 OpenAI + LangChain Tools로 구현합니다.
Gemini API는 같은 질문에 대해 도구 결과 요약 또는 개념 설명을 확인하는 보조 메뉴로 제공합니다.
"""

# common 모듈에서 Gemini 클라이언트와 모델명, 키 확인 함수를 가져옵니다.
from common import GEMINI_MODEL, get_genai_client, has_key

# Vector DB 검색 함수를 가져옵니다.
from app.services.vector_db import search_vector_db


def ask_gemini_with_context(question: str) -> str:
    """Vector DB 검색 결과를 함께 넣어 Gemini에게 답변을 요청합니다."""
    # Gemini API 키가 없으면 안내 문자열을 반환합니다.
    if not has_key("GOOGLE_API_KEY"):
        return "GOOGLE_API_KEY가 설정되어 있지 않아 Gemini API를 실행하지 않았습니다."

    # 질문과 관련된 문서 검색 결과를 가져옵니다.
    docs = search_vector_db(question, top_k=3)

    # 검색 결과를 프롬프트에 넣기 좋은 문자열로 변환합니다.
    context = "\n\n".join([f"[{d['source']}]\n{d['text']}" for d in docs])

    # Gemini 클라이언트를 생성합니다.
    client = get_genai_client()

    # Gemini에 전달할 프롬프트를 구성합니다.
    prompt = (
        "아래 참고 문서를 바탕으로 사용자의 질문에 한국어로 답하라.\n\n"
        f"[참고 문서]\n{context}\n\n"
        f"[질문]\n{question}"
    )

    # Gemini 모델을 호출합니다.
    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)

    # 응답 텍스트를 반환합니다.
    return response.text
