"""상품 추천 (임베딩 코사인).

music_recommend의 감성벡터→코사인 top_k 아이디어를 상품 도메인으로 전환한다.
Phase 5의 로컬 ko-sroberta 임베딩(정규화)을 재사용해 상품명과 질의의 코사인
유사도로 추천한다. 정규화 임베딩이므로 내적 = 코사인.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.errors import ConfigError, ValidationErr
from app.db.models import Product
from app.rag.embeddings import get_embeddings


def recommend_products(db: Session, query: str, top_k: int = 3) -> dict[str, Any]:
    if not query or not query.strip():
        raise ValidationErr("추천 질의가 비어 있습니다.")
    if top_k < 1:
        raise ValidationErr("top_k는 1 이상이어야 합니다.")

    products = db.query(Product).all()
    if not products:
        return {"query": query, "count": 0, "results": []}

    embeddings = get_embeddings()
    names = [f"{p.name} ({p.category})" for p in products]
    doc_vecs = embeddings.embed_documents(names)  # 정규화됨
    q_vec = embeddings.embed_query(query)
    # 임베딩 개수가 상품 수와 다르면 조용히 진행하지 않고 명시적 실패
    if len(doc_vecs) != len(products):
        raise ConfigError("상품 임베딩 개수가 상품 수와 일치하지 않습니다.")

    def _cos(a: list[float], b: list[float]) -> float:
        # 정규화 벡터라 내적이 곧 코사인
        return sum(x * y for x, y in zip(a, b))

    scored = [
        {"code": p.product_code, "name": p.name, "category": p.category, "score": round(_cos(q_vec, dv), 4)}
        for p, dv in zip(products, doc_vecs)
    ]
    scored.sort(key=lambda r: r["score"], reverse=True)
    top = scored[:top_k]
    return {"query": query, "count": len(top), "results": top}
