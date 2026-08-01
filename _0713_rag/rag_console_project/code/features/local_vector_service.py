# PyTorch만으로 간단한 로컬 문서 벡터와 코사인 유사도 검색을 구현합니다.
import hashlib
import re
import torch
from langchain_core.documents import Document

VECTOR_SIZE = 512


def tokenize(text: str) -> list[str]:
    """한글, 영문, 숫자로 이루어진 2글자 이상의 토큰을 추출합니다."""
    return re.findall(r"[가-힣A-Za-z0-9]{2,}", text.lower())


def token_index(token: str) -> int:
    """문자열 토큰을 항상 같은 벡터 위치로 변환합니다."""
    digest = hashlib.sha256(token.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], byteorder="big") % VECTOR_SIZE


def embed_text(text: str) -> torch.Tensor:
    """해시 기반 단어 빈도 벡터를 만들고 L2 정규화합니다."""
    vector = torch.zeros(VECTOR_SIZE, dtype=torch.float32)
    for token in tokenize(text):
        vector[token_index(token)] += 1.0
    norm = torch.linalg.vector_norm(vector)
    if norm > 0:
        vector = vector / norm
    return vector


def search_documents(query: str, docs: list[Document], top_k: int = 3) -> list[tuple[Document, float]]:
    """질문과 각 문서 벡터의 코사인 유사도를 계산해 상위 문서를 반환합니다."""
    if not docs:
        return []
    query_vector = embed_text(query)
    document_matrix = torch.stack([embed_text(doc.page_content) for doc in docs])
    scores = torch.mv(document_matrix, query_vector)
    actual_k = min(max(top_k, 1), len(docs))
    values, indices = torch.topk(scores, k=actual_k)
    return [(docs[index], float(score)) for score, index in zip(values.tolist(), indices.tolist())]
