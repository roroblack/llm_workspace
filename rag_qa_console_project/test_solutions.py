# -*- coding: utf-8 -*-
"""실습해답 검증 (answer_fn 스텁 주입, GOOGLE_API_KEY 불필요).

answer()는 실키가 필요하므로, 채점 로직(grade)은 스텁 answer_fn으로 검증한다.
실사용에서는 grade()가 실제 rag_service.answer를 호출한다.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "code"))

from solutions import GRADING_SET, grade  # noqa: E402


def _stub(correct: bool):
    mapping = {item["question"]: (item["expect"] if correct else "모르겠습니다") for item in GRADING_SET}

    def fn(question: str) -> dict:
        return {"answer": f"문서에 따르면 정답은 {mapping[question]} 입니다.", "sources": [{"source": "policy.pdf"}]}

    return fn


def main() -> None:
    assert len(GRADING_SET) == 3, "채점 세트는 3문항"

    # 정답 스텁 → 3/3
    ok = grade(_stub(True))
    assert ok["score"] == "3/3", ok
    print("[정답 스텁] 채점:", ok["score"])

    # 오답 스텁 → 0/3
    ng = grade(_stub(False))
    assert ng["passed"] == 0, ng
    print("[오답 스텁] 채점:", ng["score"])

    # 콤마 표기 정규화 확인 (answer가 '10,000원'이어도 expect '10000' 매칭)
    def comma_fn(q):
        return {"answer": "제주 왕복 배송비는 10,000원 입니다.", "sources": []}

    one = grade(comma_fn)
    jeju = [d for d in one["details"] if d["expect"] == "10000"][0]
    assert jeju["ok"] is True, one

    # 단위 포함(4,000Pa / 180분) 매칭 확인
    def unit_fn(q):
        m = {"4000": "흡입력은 4,000Pa 입니다.", "180": "최대 180분 주행합니다.", "10000": "왕복 10,000원"}
        for item in GRADING_SET:
            if item["question"] == q:
                return {"answer": m[item["expect"]], "sources": []}
        return {"answer": "", "sources": []}

    assert grade(unit_fn)["passed"] == 3, "4,000Pa·180분·10,000원 모두 통과해야 함"

    # 부분매칭 오탐 방지: '1800분'/'14000'은 '180'/'4000'과 매칭되면 안 됨
    def false_fn(q):
        m = {"4000": "흡입력은 14000 입니다.", "180": "1800분 주행합니다.", "10000": "배송비는 100000원"}
        for item in GRADING_SET:
            if item["question"] == q:
                return {"answer": m[item["expect"]], "sources": []}
        return {"answer": "", "sources": []}

    assert grade(false_fn)["passed"] == 0, "부분매칭 오탐이 없어야 함(1800!=180, 14000!=4000)"
    print("[오탐방지] 1800분≠180, 14000≠4000 확인")

    print("RAG_QA_SOLUTIONS_OK")


if __name__ == "__main__":
    main()
