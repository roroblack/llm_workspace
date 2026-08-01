# -*- coding: utf-8 -*-
"""제22강 실습문제 해답을 메뉴에서 직접 실행하기 위한 모듈입니다."""

# 선택된 LLM 공급자를 사용하기 위해 공통 모듈을 가져옵니다.
from common import get_chat
# 공급자 설정값을 읽습니다.
from app_context import get_provider
# 경쟁사 CSV 기반 실습 1 구현을 재사용합니다.
from data_report_service import make_competitor_report
# 검색과 폴백 구현을 재사용합니다.
from deep_research import search_one
# 응답 객체의 본문을 문자열로 통일합니다.
from message_utils import extract_text
# 실습 2 결과도 파일로 저장하기 위해 공통 저장 함수를 사용합니다.
from research_service import save_report


def exercise_1_competitor_csv():
    """실습문제 1: 웹 검색 없이 경쟁사 CSV 기반 리포트를 생성합니다."""
    # 실제 구현 함수가 분석, 저장, 경쟁사 검증을 모두 수행합니다.
    return make_competitor_report()


def research_multi(topic: str, subtopics: list[str]) -> tuple[str, int]:
    """실습문제 2: 미리 정한 여러 하위 질의를 각각 조사한 뒤 통합합니다."""
    # 하위 질의별 결과를 저장할 리스트를 준비합니다.
    findings: list[tuple[str, str, bool]] = []

    # 사용자가 지정한 하위 주제를 순서대로 처리합니다.
    for index, subtopic in enumerate(subtopics, start=1):
        # 원 주제와 하위 주제를 결합해 실제 검색어를 만듭니다.
        query = f"{topic} {subtopic}"

        # HTML 실습의 검증 조건대로 하위 질의 진행 로그를 출력합니다.
        print(f"[검색 {index}/{len(subtopics)}] {query}")

        # 검색 실패 시 자동 폴백되는 공통 함수를 호출합니다.
        result, used_fallback = search_one(query)

        # 종합 단계에서 사용할 하위 주제, 결과, 폴백 여부를 저장합니다.
        findings.append((subtopic, result, used_fallback))

    # 각 결과를 1,200자로 제한하여 프롬프트 크기를 관리합니다.
    blocks = "\n\n".join(
        f"[{subtopic}]\n[수집 방식: {'LLM 폴백' if fallback else '웹 검색'}]\n{result[:1200]}"
        for subtopic, result, fallback in findings
    )

    # 모든 하위 주제를 하나의 리포트로 종합할 LLM을 생성합니다.
    llm = get_chat(provider=get_provider(), temperature=0.3)

    # 각 하위 주제를 누락하지 않도록 출력 조건을 명시합니다.
    prompt = (
        f"주제: {topic}\n"
        "아래 하위 주제별 조사 결과를 종합해 한국어 마크다운 리포트를 작성하라. "
        "'## 개요', '## 핵심 동향', '## 하위 주제별 분석', '## 시사점' 섹션을 포함하고, "
        "각 하위 주제의 내용을 모두 명시적으로 반영하라. "
        "검색 실패로 LLM 폴백이 사용된 항목은 최신 검증이 필요하다고 표시하라.\n\n"
        f"{blocks}"
    )

    # 최종 통합 리포트 본문을 문자열로 추출합니다.
    body = extract_text(llm.invoke(prompt))

    # 하위 질의 중 폴백이 사용된 개수를 계산합니다.
    fallback_count = sum(1 for _, _, fallback in findings if fallback)

    # 최종 본문과 폴백 횟수를 반환합니다.
    return body, fallback_count


def exercise_2_multiquery():
    """실습문제 2의 기본 주제와 세 하위 질의를 실행하고 저장합니다."""
    # HTML 해답에서 제시한 기본 시장 주제를 사용합니다.
    topic = "무선이어버드 시장"

    # 기술, 가격, 경쟁 구도를 서로 다른 하위 질의로 지정합니다.
    subtopics = [
        "ANC 노이즈캔슬링 트렌드",
        "가격대 동향",
        "주요 제조사 점유율",
    ]

    # 다중 하위 질의 조사와 통합을 실행합니다.
    body, fallback_count = research_multi(topic, subtopics)

    # 실행 결과를 재확인할 수 있도록 별도 마크다운 파일에 저장합니다.
    path = save_report(topic, body, prefix="exercise_multiquery")

    # 메뉴 화면에서 출력할 모든 결과를 반환합니다.
    return body, path, subtopics, fallback_count
