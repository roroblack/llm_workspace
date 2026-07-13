# -*- coding: utf-8 -*-
"""실습해답 검증 (API 키 불필요)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "code"))

from solutions import chunk_size_comparison, chunk_text  # noqa: E402


def main() -> None:
    # 문제 1: 겹침 50자 동일
    text = "".join(chr(0xAC00 + (i % 100)) for i in range(1500))  # 한글 1500자
    chunks = chunk_text(text, size=500, overlap=50)
    assert len(chunks) >= 2, "청크가 2개 이상이어야 함"
    # 모든 인접 청크가 정확히 50자 겹침
    for i in range(len(chunks) - 1):
        assert chunks[i][-50:] == chunks[i + 1][:50], f"{i}/{i+1} 청크 겹침 불일치"
    # 전체 커버 확인(마지막 청크가 끝까지)
    assert chunks[-1].endswith(text[-1]), "마지막 청크가 원문 끝을 포함해야 함"
    # 재조합으로 원문 복원 가능(겹침 제거 후 이어붙임)
    rebuilt = chunks[0] + "".join(c[50:] for c in chunks[1:])
    assert rebuilt == text, "겹침 제거 후 이어붙이면 원문과 동일해야 함"
    print(f"[문제1] OK 청크수={len(chunks)}, 모든 인접 겹침50자 동일=True, 원문복원=True")

    # 문제 2: size 커질수록 청크 수 감소
    rows = chunk_size_comparison("A" * 3000, sizes=(200, 500, 1000), overlap=50)
    counts = [r["count"] for r in rows]
    assert counts[0] > counts[1] > counts[2], f"size↑ → count↓ 이어야 함: {rows}"
    print("[문제2] OK", [(r["size"], r["count"], r["avg_len"]) for r in rows])

    # 엣지: overlap >= size → ValueError
    for bad in [(10, 10), (10, 20), (0, 0)]:
        try:
            chunk_text("x" * 20, size=bad[0], overlap=bad[1])
            raise AssertionError(f"잘못된 인자 {bad}는 ValueError여야 함")
        except ValueError:
            pass

    print("RAG_CONSOLE_SOLUTIONS_OK")


if __name__ == "__main__":
    main()
