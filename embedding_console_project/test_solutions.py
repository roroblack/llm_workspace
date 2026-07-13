# -*- coding: utf-8 -*-
"""실습해답 검증 (로컬 임베딩 주입, GOOGLE_API_KEY 불필요).

실사용은 Gemini(gemini-embedding-001)지만, 여기서는 로컬 ko-sroberta 임베딩을 주입해
most_similar / compare_pairs 로직을 오프라인으로 검증한다.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "code"))

from solutions import compare_pairs, most_similar  # noqa: E402


def _local_embeddings():
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(
        model_name="jhgan/ko-sroberta-multitask",
        encode_kwargs={"normalize_embeddings": True},
    )


def main() -> None:
    emb = _local_embeddings()

    # 문제 1: 배송 질의 → 배송 FAQ가 1위
    docs = [
        "배송은 보통 얼마나 걸리나요?",
        "환불은 어떻게 신청하나요?",
        "회원 등급 혜택이 궁금해요",
        "비밀번호를 잊어버렸어요",
    ]
    res = most_similar("배송 얼마나 걸려요?", docs, k=3, embeddings=emb)
    assert res[0]["doc"] == docs[0], f"배송 FAQ가 1위여야 함: {res}"
    assert res[0]["score"] >= res[-1]["score"], "점수 내림차순이어야 함"
    print("[문제1] OK 1위:", res[0]["doc"], f"(score {res[0]['score']})")

    # 문제 2: 유사 쌍 점수 > 무관 쌍 점수
    cmp = compare_pairs("배송이 정말 빨라요", "배송이 빠르고 좋았어요", "가격이 너무 비싸요", embeddings=emb)
    assert cmp["ok"] is True, f"유사쌍 > 무관쌍이어야 함: {cmp}"
    print("[문제2] OK", cmp)

    # 엣지: 빈 query → ValueError
    try:
        most_similar("  ", docs, embeddings=emb)
        raise AssertionError("빈 query는 ValueError여야 함")
    except ValueError:
        pass

    # 엣지: 빈 docs → 빈 리스트
    assert most_similar("배송", [], embeddings=emb) == [], "빈 docs는 []이어야 함"

    # 엣지: k가 docs 수보다 크면 docs 수만큼만 반환
    res2 = most_similar("배송", docs[:2], k=10, embeddings=emb)
    assert len(res2) == 2, f"k>len(docs)면 len(docs)개: {res2}"

    print("EMBEDDING_SOLUTIONS_OK")


if __name__ == "__main__":
    main()
