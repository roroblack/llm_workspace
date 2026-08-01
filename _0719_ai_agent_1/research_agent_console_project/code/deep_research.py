# -*- coding: utf-8 -*-
"""큰 조사 주제를 하위 질의로 분해하고 검색 결과를 종합하는 모듈입니다."""

# 구조화 출력 스키마를 정의하기 위해 Pydantic을 가져옵니다.
from pydantic import BaseModel, Field

# 제공된 공통 모듈의 LLM 생성 함수를 사용합니다.
from common import get_chat
# 사용자가 선택한 모델 공급자를 읽습니다.
from app_context import get_provider
# 모델 응답 본문을 문자열로 통일합니다.
from message_utils import extract_text
# 검색 도구 생성과 보고서 저장 기능을 재사용합니다.
from research_service import _build_search_tool, save_report


class SubQueries(BaseModel):
    """LLM이 반환해야 하는 하위 검색 질의 목록의 구조입니다."""

    # 자유 텍스트 대신 3~4개의 문자열 목록으로 결과 형식을 강제합니다.
    queries: list[str] = Field(
        description="원래 주제를 깊이 조사하기 위한 서로 겹치지 않는 한국어 검색 질의 3~4개"
    )


def split_topic(topic: str) -> list[str]:
    """큰 주제를 3~4개의 구체적이고 중복되지 않는 하위 질의로 나눕니다."""
    # 질의 분해는 일관성이 중요하므로 낮은 temperature로 LLM을 생성합니다.
    llm = get_chat(provider=get_provider(), temperature=0.2)

    # Pydantic 스키마에 맞는 구조화 출력을 요청합니다.
    structured_llm = llm.with_structured_output(SubQueries)

    # 시장 규모, 기술, 가격, 경쟁 구도 등 서로 다른 관점이 나오도록 지시합니다.
    prompt = (
        f"너는 시장 조사 계획을 세우는 애널리스트다. 주제 '{topic}'를 깊이 조사하기 위해 "
        "서로 겹치지 않는 구체적 한국어 검색 질의 3~4개로 분해하라. "
        "가능하면 시장 규모·성장, 기술 또는 제품, 가격 또는 소비자, 주요 기업 또는 경쟁 구도를 나누어라. "
        "각 항목은 검색창에 그대로 넣을 수 있는 짧은 질의여야 한다."
    )

    try:
        # 구조화된 SubQueries 객체를 받아 최대 4개만 사용합니다.
        result = structured_llm.invoke(prompt)
        # 빈 문자열을 제거하고 앞뒤 공백을 정리합니다.
        queries = [query.strip() for query in result.queries if query.strip()]
        # 최소 2개 이상의 유효 질의가 있을 때만 정상 결과로 사용합니다.
        if len(queries) >= 2:
            return queries[:4]
    except Exception as exc:
        # 구조화 출력이 지원되지 않거나 호출이 실패하면 폴백 질의를 사용합니다.
        print(f"[경고] 하위 질의 자동 분해 실패 → 기본 질의 사용: {exc}")

    # 전체 조사가 멈추지 않도록 범용 하위 질의 세 개를 반환합니다.
    return [
        f"{topic} 시장 규모 성장률 최신 동향",
        f"{topic} 기술 제품 기능 트렌드",
        f"{topic} 가격 소비자 선호 주요 기업 경쟁",
    ]


def search_one(query: str) -> tuple[str, bool]:
    """하위 질의 하나를 검색하고 실패하면 LLM 지식으로 대체합니다."""
    try:
        # DuckDuckGo 검색 도구를 생성합니다.
        search_tool = _build_search_tool()
        # 질의를 실행해 스니펫과 링크가 포함된 검색 결과를 문자열로 반환합니다.
        return str(search_tool.invoke(query)), False
    except Exception as exc:
        # 한 질의의 실패가 전체 조사를 중단시키지 않도록 경고만 출력합니다.
        print(f"  [경고] 검색 실패('{query}') → LLM 지식 폴백: {exc}")

        # 선택한 공급자의 LLM으로 해당 하위 질의에 대한 임시 사실을 생성합니다.
        llm = get_chat(provider=get_provider(), temperature=0.3)

        # 최신 정보가 아닐 수 있음을 명시하고 근거 없는 수치를 만들지 않게 합니다.
        prompt = (
            f"'{query}'에 대해 아는 범위에서 핵심 내용을 한국어로 3~5개 정리하라. "
            "웹 검색을 사용하지 못했으므로 최신 정보가 아닐 수 있음을 표시하고, "
            "확인되지 않은 구체적 수치는 만들지 마라."
        )

        # 폴백 사용 여부 True와 함께 본문을 반환합니다.
        return extract_text(llm.invoke(prompt)), True


def synthesize(topic: str, findings: list[tuple[str, str, bool]]) -> str:
    """하위 질의별 검색 결과를 하나의 마크다운 시장 리포트로 종합합니다."""
    # 리포트 작성에는 약간의 서술력이 필요하므로 temperature 0.3을 사용합니다.
    llm = get_chat(provider=get_provider(), temperature=0.3)

    # 각 검색 결과를 1,500자로 제한해 지나친 토큰 사용을 막습니다.
    blocks = "\n\n".join(
        (
            f"[하위 질의] {query}\n"
            f"[수집 방식] {'LLM 폴백' if fallback else '웹 검색'}\n"
            f"{result[:1500]}"
        )
        for query, result, fallback in findings
    )

    # 모든 하위 질의를 빠짐없이 반영하고 폴백 내용을 구분하도록 지시합니다.
    prompt = (
        f"주제: {topic}\n\n"
        "아래는 하위 질의별 조사 결과다. 서로 중복되는 내용을 합치고 상충하는 내용은 불확실하다고 표시하라. "
        "한국어 마크다운 리포트로 작성하며 '## 개요', '## 핵심 동향', '## 세부 분석', "
        "'## 시사점', '## 조사 한계' 섹션을 정확히 포함하라. "
        "각 하위 질의의 핵심을 모두 반영하고, LLM 폴백 결과는 최신 검증이 필요하다고 표시하라.\n\n"
        f"{blocks}"
    )

    # 종합 리포트 문자열을 반환합니다.
    return extract_text(llm.invoke(prompt))


def deep_research(topic: str) -> tuple[str, list[str], int]:
    """주제 분해 → 개별 검색 → 종합의 전체 심층 조사 파이프라인을 실행합니다."""
    # 1단계로 큰 주제를 하위 검색 질의로 분해합니다.
    queries = split_topic(topic)

    # 진행 상황을 사용자가 확인할 수 있도록 질의 개수를 출력합니다.
    print(f"[분해] {len(queries)}개 하위 질의")

    # 각 하위 질의의 순서와 내용을 출력합니다.
    for index, query in enumerate(queries, start=1):
        print(f"  [{index}] {query}")

    # 검색 결과, 질의, 폴백 여부를 모을 리스트입니다.
    findings: list[tuple[str, str, bool]] = []

    # 생성된 하위 질의를 하나씩 검색합니다.
    for index, query in enumerate(queries, start=1):
        print(f"[검색 {index}/{len(queries)}] {query}")
        result, used_fallback = search_one(query)
        findings.append((query, result, used_fallback))

    # 하위 질의 중 폴백이 사용된 횟수를 계산합니다.
    fallback_count = sum(1 for _, _, used_fallback in findings if used_fallback)

    # 모든 결과를 하나의 보고서로 종합합니다.
    body = synthesize(topic, findings)

    # 본문, 하위 질의 목록, 폴백 횟수를 반환합니다.
    return body, queries, fallback_count


def deep_research_and_save(topic: str):
    """심층 조사 결과를 생성하고 마크다운 파일에 저장합니다."""
    # 전체 심층 조사 파이프라인을 실행합니다.
    body, queries, fallback_count = deep_research(topic)

    # 일반 리포트와 구분되도록 deep_research 접두어로 저장합니다.
    path = save_report(topic, body, prefix="deep_research")

    # 메뉴 화면에서 사용할 결과를 반환합니다.
    return body, path, queries, fallback_count
