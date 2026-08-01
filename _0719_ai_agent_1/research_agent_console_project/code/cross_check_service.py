# -*- coding: utf-8 -*-
"""동일한 주장을 서로 다른 검색어로 조사하여 교차 검증하는 모듈입니다."""

# 교차 검증 판정을 구조화하기 위해 Pydantic을 가져옵니다.
from pydantic import BaseModel, Field

# 공통 모듈에서 LLM 생성 함수를 가져옵니다.
from common import get_chat
# 선택한 OpenAI 또는 Gemini 공급자 값을 가져옵니다.
from app_context import get_provider
# 검색 함수는 심층 조사 모듈의 안정적인 폴백 구현을 재사용합니다.
from deep_research import search_one


class Verdict(BaseModel):
    """교차 검증 결과의 고정된 출력 구조입니다."""

    # 두 검색 결과의 관계를 세 범주 중 하나로 표현합니다.
    agree: str = Field(description="일치, 부분일치, 불일치 중 하나")
    # 전체 근거 수준을 세 단계로 표현합니다.
    confidence: str = Field(description="높음, 보통, 낮음 중 하나")
    # 최종 판단 이유를 한국어 문장으로 저장합니다.
    reason: str = Field(description="판단 근거를 설명하는 한국어 1~3문장")
    # 추가 확인이 필요한 내용을 명시합니다.
    caution: str = Field(description="추가 확인 사항 또는 주의점")


def cross_check(claim: str, query_a: str, query_b: str) -> tuple[Verdict, str, str, int]:
    """한 주장을 두 검색어로 조사하고 일치 여부와 신뢰도를 판정합니다."""
    # 첫 번째 검색어로 근거를 수집합니다.
    result_a, fallback_a = search_one(query_a)

    # 두 번째로 표현이 다른 검색어를 사용해 독립적인 근거를 수집합니다.
    result_b, fallback_b = search_one(query_b)

    # 판정 결과는 일관성이 중요하므로 temperature 0으로 모델을 생성합니다.
    llm = get_chat(provider=get_provider(), temperature=0.0)

    # 자유로운 문장 대신 Verdict 구조에 맞춘 응답을 요청합니다.
    structured_llm = llm.with_structured_output(Verdict)

    # 검색 결과가 너무 길어지는 것을 막기 위해 각각 1,500자까지만 전달합니다.
    prompt = (
        f"검증할 주장: {claim}\n\n"
        f"[검색 A: {query_a}]\n{result_a[:1500]}\n\n"
        f"[검색 B: {query_b}]\n{result_b[:1500]}\n\n"
        "두 결과가 주장을 지지하는지 비교하라. 출처가 약하거나 서로 어긋나거나 "
        "검색 대신 LLM 폴백이 포함되었다면 신뢰도를 보수적으로 낮춰라. "
        "agree는 반드시 '일치', '부분일치', '불일치' 중 하나로, "
        "confidence는 반드시 '높음', '보통', '낮음' 중 하나로 작성하라."
    )

    try:
        # 구조화된 교차 검증 결과를 생성합니다.
        verdict = structured_llm.invoke(prompt)
    except Exception as exc:
        # 판정 실패 시 잘못된 높은 신뢰도를 주지 않도록 보수적인 결과를 생성합니다.
        verdict = Verdict(
            agree="불일치",
            confidence="낮음",
            reason=f"구조화 판정 과정에서 오류가 발생했습니다: {exc}",
            caution="검색 원문과 공식 자료를 사람이 직접 다시 확인해야 합니다.",
        )

    # 두 검색 중 폴백이 사용된 횟수를 계산합니다.
    fallback_count = int(fallback_a) + int(fallback_b)

    # 판정 결과와 원문 검색 결과, 폴백 횟수를 반환합니다.
    return verdict, result_a, result_b, fallback_count
