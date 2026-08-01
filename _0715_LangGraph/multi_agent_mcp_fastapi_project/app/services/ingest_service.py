# -*- coding: utf-8 -*-
"""CSV 데이터를 Vector DB 문서로 변환해 색인합니다."""
import pandas as pd
from app.core.config import PROJECT_ROOT
from app.vectordb.chroma_store import ChromaStore

def ingest_csv_data() -> dict[str, int]:
    store = ChromaStore()
    products = pd.read_csv(PROJECT_ROOT / "data" / "products.csv")
    faq = pd.read_csv(PROJECT_ROOT / "data" / "faq.csv")
    product_docs, product_meta = [], []
    for row in products.itertuples():
        product_docs.append(f"상품명: {row.product_name}; 카테고리: {row.category}; 가격: {row.price}원; 재고: {row.stock}; 평점: {row.rating}")
        product_meta.append({"source": "products", "category": str(row.category), "product_id": str(row.product_id)})
    faq_docs, faq_meta = [], []
    for index, row in enumerate(faq.itertuples(), start=1):
        faq_docs.append(f"질문: {row.question}\n답변: {row.answer}")
        faq_meta.append({"source": "faq", "faq_id": str(index)})
    return {"products": store.upsert(product_docs, product_meta), "faq": store.upsert(faq_docs, faq_meta)}
