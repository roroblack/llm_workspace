# -*- coding: utf-8 -*-
"""ChromaDB에 상품·FAQ 문서를 저장하고 의미 검색하는 모듈입니다."""
import hashlib
import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from app.core.config import get_settings

class ChromaStore:
    def __init__(self) -> None:
        settings = get_settings()
        self.client = chromadb.PersistentClient(path=settings.chroma_path)
        # 외부 API 키가 없어도 실습 가능한 Chroma 기본 임베딩 함수를 사용합니다.
        self.embedding_function = DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(name="mall_knowledge", embedding_function=self.embedding_function)

    @staticmethod
    def _id(source: str, text: str) -> str:
        return hashlib.sha256(f"{source}:{text}".encode("utf-8")).hexdigest()[:32]

    def upsert(self, documents: list[str], metadatas: list[dict]) -> int:
        ids = [self._id(str(meta.get("source", "unknown")), doc) for doc, meta in zip(documents, metadatas, strict=True)]
        self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        return len(ids)

    def search(self, query: str, source: str | None = None, limit: int = 3) -> list[dict]:
        where = {"source": source} if source else None
        result = self.collection.query(query_texts=[query], n_results=limit, where=where)
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        return [{"document": d, "metadata": m or {}, "distance": dist} for d, m, dist in zip(docs, metas, distances, strict=False)]
