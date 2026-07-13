# -*- coding: utf-8 -*-
"""제14강 임베딩 실습문제 해답.

실습문제_embedding.txt 의 두 문제 해답을 구현한다.
- 문제 1: most_similar(query, docs, k) — 코사인 유사도 상위 k개 검색
- 문제 2: compare_pairs(...) — 유사/비유사 문장 쌍 코사인 비교

embeddings 인자를 주입할 수 있어(기본은 common.get_embeddings) 오프라인 테스트에서는
로컬 임베딩을 넣어 로직을 검증하고, 실사용에서는 Gemini(gemini-embedding-001)를 쓴다.
"""

from __future__ import annotations

import csv
from typing import Any

from common import DATA
from vector_utils import cosine_similarity, top_k_indices


def _embeddings(embeddings: Any | None):
    """주입된 임베딩이 없으면 문제 요구대로 Gemini 임베딩을 사용한다."""
    if embeddings is not None:
        return embeddings
    from common import get_embeddings

    return get_embeddings("gemini")


def most_similar(query: str, docs: list[str], k: int = 3, embeddings: Any | None = None) -> list[dict]:
    """query와 docs를 임베딩해 코사인 유사도 상위 k개를 반환한다.

    반환: [{"index", "doc", "score"}] (score 내림차순)
    """
    if not query or not query.strip():
        raise ValueError("query가 비어 있습니다.")
    if not docs:
        return []
    emb = _embeddings(embeddings)
    doc_vecs = emb.embed_documents(docs)
    query_vec = emb.embed_query(query)
    ranked = top_k_indices(query_vec, doc_vecs, k)
    return [{"index": i, "doc": docs[i], "score": round(score, 4)} for i, score in ranked]


def compare_pairs(
    similar_a: str, similar_b: str, unrelated: str, embeddings: Any | None = None
) -> dict:
    """유사한 문장 쌍과 무관한 문장 쌍의 코사인 유사도를 비교한다.

    반환: {"similar_score", "unrelated_score", "ok"} (ok = 유사 쌍 점수 > 무관 쌍 점수)
    """
    emb = _embeddings(embeddings)
    vec_a, vec_b, vec_u = emb.embed_documents([similar_a, similar_b, unrelated])
    similar_score = cosine_similarity(vec_a, vec_b)
    unrelated_score = cosine_similarity(vec_a, vec_u)
    return {
        "similar_score": round(similar_score, 4),
        "unrelated_score": round(unrelated_score, 4),
        "ok": similar_score > unrelated_score,
    }


def _load_column(csv_name: str, column: str) -> list[str]:
    path = DATA / csv_name
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [row[column] for row in csv.DictReader(f)]


def run_demo(embeddings: Any | None = None) -> None:
    """faq.csv / reviews.csv로 두 문제를 시연한다 (기본 Gemini, 키 필요)."""
    # 문제 1: FAQ 질문에서 배송 관련 질의 검색
    questions = _load_column("faq.csv", "question")
    print("[문제1] '배송 얼마나 걸려요?' Top-3")
    for r in most_similar("배송 얼마나 걸려요?", questions, k=3, embeddings=embeddings):
        print(f"  {r['score']:.4f}  {r['doc']}")

    # 문제 2: 의미가 비슷한 리뷰 2개(같은 주제) vs 무관한 리뷰 1개를 골라 비교
    reviews = _load_column("reviews.csv", "review_text")
    delivery = [r for r in reviews if "배송" in r]  # 배송 주제(유사)
    other = [r for r in reviews if "배송" not in r and "가격" in r] or [
        r for r in reviews if "배송" not in r
    ]  # 배송과 무관
    if len(delivery) >= 2 and other:
        result = compare_pairs(delivery[0], delivery[1], other[0], embeddings=embeddings)
        print(f"\n[문제2] 유사쌍('{delivery[0][:12]}..','{delivery[1][:12]}..') vs 무관('{other[0][:12]}..')")
        print("       ", result)
    else:
        print("\n[문제2] 배송 주제 리뷰가 부족해 시연을 건너뜁니다.")


if __name__ == "__main__":
    run_demo()
