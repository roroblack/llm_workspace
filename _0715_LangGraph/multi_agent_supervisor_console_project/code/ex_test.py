# -*- coding: utf-8 -*-
"""문제 2 — 3-way 규칙 라우터 정확도 테스트.

ex_three.route_rule_3way를 (질문, 기대route) 6쌍(각 에이전트당 2개)으로 평가하여
"정확도: N/6"을 출력하고, 오분류된 질문을 함께 표시합니다.
외부 API를 호출하지 않으므로 API 키 없이 완전 오프라인으로 검증됩니다.
"""

from __future__ import annotations

import sys
from pathlib import Path

# 직접 실행과 모듈 실행 모두에서 code 폴더를 찾도록 경로를 보정합니다.
CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

# 평가 대상인 3-way 규칙 라우터를 가져옵니다.
from ex_three import route_rule_3way

# (질문, 기대 라우트) 6쌍 — sales / policy / competitor 각 2개씩 구성합니다.
CASES: tuple[tuple[str, str], ...] = (
    # competitor 2개
    ("경쟁사랑 비교하면 어때?", "competitor"),
    ("타사 대비 우리 강점이 뭐야?", "competitor"),
    # policy 2개
    ("환불은 며칠 안에 신청해야 해?", "policy"),
    ("무료배송 기준이 어떻게 돼?", "policy"),
    # sales 2개
    ("전자기기 추천 좀 해줘", "sales"),
    ("가성비 좋은 상품 골라줘", "sales"),
)


def evaluate() -> tuple[int, list[tuple[str, str, str]]]:
    """각 질문을 규칙 라우터에 통과시켜 맞힌 개수와 오분류 목록을 반환합니다."""
    # 맞힌 개수를 셀 카운터를 준비합니다.
    correct = 0

    # (질문, 기대, 실제) 형태의 오분류 항목을 저장할 리스트를 준비합니다.
    wrong: list[tuple[str, str, str]] = []

    # 모든 평가 케이스를 순회합니다.
    for question, expected in CASES:
        # 규칙 라우터의 실제 분류 결과를 얻습니다.
        actual = route_rule_3way(question).target

        # 기대값과 실제값을 비교하여 카운트하거나 오분류로 기록합니다.
        if actual == expected:
            correct += 1
        else:
            wrong.append((question, expected, actual))

    # 맞힌 개수와 오분류 목록을 반환합니다.
    return correct, wrong


def main() -> None:
    """정확도와 오분류 내역을 출력합니다."""
    # 라우터 평가를 실행합니다.
    correct, wrong = evaluate()

    # 요구된 형식으로 정확도를 출력합니다.
    print(f"정확도: {correct}/{len(CASES)}")

    # 오분류가 있으면 각 항목을 상세히 표시합니다.
    if wrong:
        print("\n[오분류된 질문]")
        for question, expected, actual in wrong:
            print(f"[X] {question} | 기대={expected} | 실제={actual}")
    else:
        # 오분류가 없으면 전부 정확함을 알립니다.
        print("모든 질문이 정확히 분류되었습니다.")


if __name__ == "__main__":
    main()
