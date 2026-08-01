# -*- coding: utf-8 -*-
"""제13강 RAG 청킹 실습문제 해답 (API 키 불필요).

실습문제_rag개념.txt 의 두 문제 해답.
- 문제 1: chunk_text(text, size, overlap) — 글자 수 기준 겹침 청킹 직접 구현
- 문제 2: chunk_size_comparison(...) — size별 청크 수·평균 길이 비교
"""

from __future__ import annotations


def chunk_text(text: str, size: int = 500, overlap: int = 50) -> list[str]:
    """글자 수 기준으로 자르되 overlap만큼 겹치게 나눈다.

    overlap > 0이면 연속한 두 청크는 정확히 overlap 글자만큼 겹친다:
    chunk[i][-overlap:] == chunk[i+1][:overlap]
    (overlap == 0이면 겹침이 없다.)
    """
    if size <= 0:
        raise ValueError("size는 1 이상이어야 합니다.")
    if not (0 <= overlap < size):
        raise ValueError("overlap은 0 이상이고 size보다 작아야 합니다.")
    if not text:
        return []

    step = size - overlap
    chunks: list[str] = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + size])
        # 마지막(전체를 덮은) 청크면 종료
        if start + size >= len(text):
            break
        start += step
    return chunks


def chunk_size_comparison(
    text: str, sizes: tuple[int, ...] = (200, 500, 1000), overlap: int = 50
) -> list[dict]:
    """size를 바꿔가며 청크 개수와 평균 길이를 표(리스트)로 반환한다."""
    rows: list[dict] = []
    for size in sizes:
        used_overlap = min(overlap, size - 1)
        chunks = chunk_text(text, size, used_overlap)
        avg = round(sum(len(c) for c in chunks) / len(chunks), 1) if chunks else 0.0
        rows.append({"size": size, "overlap": used_overlap, "count": len(chunks), "avg_len": avg})
    return rows


def _extract_pdf_text(file_name: str) -> str:
    """docs 폴더의 PDF에서 텍스트를 추출한다 (문제 예시 파일용)."""
    from common import DOCS
    from langchain_community.document_loaders import PyPDFLoader

    pages = PyPDFLoader(str(DOCS / file_name)).load()
    return "\n".join(p.page_content for p in pages)


def run_demo() -> None:
    """직원핸드북/환불교환정책 PDF로 두 문제를 시연한다."""
    # 문제 1: 겹침 검증
    text = _extract_pdf_text("직원핸드북.pdf")
    chunks = chunk_text(text, size=500, overlap=50)
    print(f"[문제1] 청크 수: {len(chunks)}")
    if len(chunks) >= 2:
        same = chunks[0][-50:] == chunks[1][:50]
        print(f"  첫/둘째 청크 겹침 50자 동일: {same}")

    # 문제 2: size 비교
    policy = _extract_pdf_text("환불교환정책.pdf")
    print("\n[문제2] size별 비교")
    print(f"  {'size':>6} {'청크수':>6} {'평균길이':>8}")
    for row in chunk_size_comparison(policy):
        print(f"  {row['size']:>6} {row['count']:>6} {row['avg_len']:>8}")
    print("  결론: 조항 단위 검색에는 200~500자가 적합(조항이 섞이지 않게 작게).")


if __name__ == "__main__":
    run_demo()
