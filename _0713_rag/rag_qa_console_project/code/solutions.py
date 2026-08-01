# -*- coding: utf-8 -*-
"""제16강 RAG QA 실습문제 해답.

실습문제_rag_qa.txt 의 두 문제 해답.
- 문제 1: answer(question) → {"answer":..., "sources":[...]}  (rag_service.answer 재사용)
- 문제 2: grade() — 정답이 정해진 질문 3개로 answer() 결과를 자동 채점

answer()는 GOOGLE_API_KEY가 필요하다(임베딩+LLM). grade()는 answer_fn을 주입할 수 있어
오프라인 테스트에서는 스텁으로 채점 로직을 검증하고, 실사용에서는 실제 answer()를 쓴다.
"""

from __future__ import annotations

import re
from typing import Any, Callable

# 문제 1 해답: rag_service.answer 가 이미 {"answer", "sources"} 형태로 반환한다.
from rag_service import answer  # noqa: F401  (실습 해답의 핵심 함수)

# 문제 2 해답: 정책/매뉴얼 PDF에서 답이 정해진 질문과 정답
GRADING_SET: list[dict[str, str]] = [
    # 제품매뉴얼_로봇청소기.pdf
    {"question": "로봇청소기 CleanX(GCX-100)의 흡입력은 얼마인가요?", "expect": "4000"},
    {"question": "CleanX 로봇청소기의 최대 주행시간은 몇 분인가요?", "expect": "180"},
    # 환불교환정책.pdf
    {"question": "제주 지역 단순변심 반품의 왕복 배송비는 얼마인가요?", "expect": "10000"},
]


def _extract_numbers(text: str) -> set[str]:
    """텍스트에서 콤마를 제거한 뒤 온전한 숫자 토큰만 추출한다.

    부분매칭 오탐 방지: '1800분'은 {'1800'}, '14000원'은 {'14000'}이 되어
    기대값 '180'/'4000'과 잘못 매칭되지 않는다.
    """
    return set(re.findall(r"\d+", text.replace(",", "")))


def _matches(expect: str, text: str) -> bool:
    """기대값이 숫자면 온전한 숫자 일치로, 아니면 부분 문자열로 판정한다."""
    if expect.replace(",", "").isdigit():
        return expect.replace(",", "") in _extract_numbers(text)
    return expect in text


def grade(answer_fn: Callable[[str], dict[str, Any]] | None = None) -> dict[str, Any]:
    """GRADING_SET으로 answer() 결과가 정답을 포함하는지 자동 채점한다.

    숫자 정답은 온전한 숫자 일치(부분매칭 오탐 방지)로 채점한다.
    반환: {"score": "2/3", "passed", "total", "details"}
    """
    answer_fn = answer_fn or (lambda q: answer(q))
    details: list[dict[str, Any]] = []
    passed = 0
    for item in GRADING_SET:
        result = answer_fn(item["question"])
        text = result.get("answer", "") if isinstance(result, dict) else str(result)
        ok = _matches(item["expect"], text)
        passed += 1 if ok else 0
        details.append({"question": item["question"], "expect": item["expect"], "ok": ok})
    return {
        "score": f"{passed}/{len(GRADING_SET)}",
        "passed": passed,
        "total": len(GRADING_SET),
        "details": details,
    }


def run_demo() -> None:
    """실제 answer()로 문제1 예시와 문제2 채점을 시연한다 (GOOGLE_API_KEY 필요)."""
    # 문제 1
    result = answer("제주 지역 반품 배송비는 얼마인가요?")
    print("[문제1] answer:", result["answer"])
    print("        sources:", [s["source"] for s in result["sources"]])

    # 문제 2
    report = grade()
    print("\n[문제2] 채점:", report["score"])
    for d in report["details"]:
        print(f"  {'O' if d['ok'] else 'X'} {d['question']} (기대 {d['expect']})")


if __name__ == "__main__":
    run_demo()
