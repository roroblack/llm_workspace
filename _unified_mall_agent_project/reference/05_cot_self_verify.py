# -*- coding: utf-8 -*-
"""[복습 05] Chain-of-Thought · 자기검증(self-verification)

원본: cot_console_project/src/llm_clients.py  (강의 PDF 0710 ReAct/Reasoning)
공략집 스테이지 9

■ 핵심
  - 직접 답변: "설명 없이 최종 숫자만"
  - CoT: "단계적으로 풀고 마지막 줄에 '정답: <숫자>'" → 계산/추론에서 정확도가 오르는 경향
    (항상 보장 X — 모델·문제에 따라 장황·비용↑·오류 고착도 있음)
  - 자기검증: 제출 풀이를 다시 검산. 단, **같은 모델의 재검증은 '독립' 검증이 아니다.**
    진짜 검증이 필요하면 계산기·코드·규칙 같은 외부 검증기가 더 강하다.
  - CoT를 끄는 경우(중요): 단순 질문(토큰 낭비), 함정 문제(장황한 추론이 오답 유도)

■ 통합 앱: app/prompts/templates.py 에 build_cot_prompt/should_use_cot 로 반영됨.
  여기선 3단(직접/CoT/검증)을 나란히 비교하며 복습.
"""

from __future__ import annotations

import re


def direct_prompt(question: str) -> str:
    return f"다음 문제의 최종 숫자만 출력하라(설명 없이):\n{question}"


def cot_prompt(question: str) -> str:
    return f"다음 문제를 단계적으로 풀어라. 마지막 줄에 '정답: <숫자>' 형식으로 답하라.\n{question}"


def verify_prompt(question: str, submitted_solution: str) -> str:
    return (
        "아래 제출된 풀이가 맞는지 검산하라. 틀렸으면 올바른 풀이와 정답을, "
        "맞으면 '검증 완료'와 정답을 마지막 줄에 '정답: <숫자>'로 제시하라.\n\n"
        f"[문제]\n{question}\n\n[제출된 풀이]\n{submitted_solution}"
    )


def should_use_cot(question: str) -> bool:
    """CoT 사용 여부 휴리스틱(학습용). 짧고 단순하면 끈다."""
    q = question.strip()
    if len(q) < 15:
        return False
    return any(s in q for s in ["몇", "계산", "얼마", "왜", "총", "합", "차이", "비교"])


def extract_answer_number(text: str) -> str | None:
    """모델 출력에서 마지막 숫자(정답)를 추출한다."""
    nums = re.findall(r"-?\d[\d,]*", text.replace(" ", ""))
    return nums[-1].replace(",", "") if nums else None


if __name__ == "__main__":
    q = "사과 3개에 1200원씩, 배 2개에 1500원씩이면 총 얼마인가?"
    print("CoT 사용?", should_use_cot(q))          # True (계산 신호)
    print("CoT 사용?(단순)", should_use_cot("안녕"))  # False
    print("\n[직접]\n", direct_prompt(q))
    print("\n[CoT]\n", cot_prompt(q))
    print("\n정답 추출 예:", extract_answer_number("... 따라서 정답: 6,600"))  # 6600
