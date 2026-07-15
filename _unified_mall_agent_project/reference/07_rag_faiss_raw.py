# -*- coding: utf-8 -*-
"""[복습 07] RAG 날것 — 청킹 → 임베딩 → FAISS → 검색 (인덱싱/서비스 분리)

원본: vector_db_pycharm_project/src/  (강의 PDF 0708 VectorDB)
공략집 스테이지 12

■ 통합 앱: app/rag/ 에 잘 반영됨. 여기선 "RAG 파이프라인 최소 골격"과
  PDF4가 강조한 두 원칙을 한 파일로 복습한다.

■ 두 핵심 원칙
  1) 인덱싱(사전 1회) vs 서비스(요청 시 로드만) 분리
     - build_index(): 청킹→임베딩→save_local (한 번)
     - search(): load_local(한 번 캐시) 후 검색만. "요청마다 from_documents" 금지!
  2) FAISS 점수 = 거리(distance), 작을수록 유사 (코사인 유사도와 반대) → 정렬 주의
     · FAISS 기본은 L2(제곱 유클리드). 정규화 벡터면 값 범위는 대략 [0,4](0=동일).
       "작을수록 유사"는 이 기본 구성에서 성립. 다른 index/metric이면 규칙이 달라진다.

■ 실행에 필요: sentence-transformers(로컬 임베딩), faiss-cpu, langchain-community
  (통합 프로젝트 requirements에 이미 포함)
"""

from __future__ import annotations

from pathlib import Path


def get_embeddings():
    """로컬 임베딩(토큰0). 정규화하면 거리가 [0,2]로 유계 → 임계값이 의미를 가짐."""
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(
        model_name="jhgan/ko-sroberta-multitask",
        encode_kwargs={"normalize_embeddings": True},
    )


def build_index(texts: list[str], out_dir: str) -> None:
    """[인덱싱: 사전 1회] 청킹→임베딩→FAISS→디스크 저장."""
    from langchain_community.vectorstores import FAISS
    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    docs = [Document(page_content=t, metadata={"source": f"doc{i}"}) for i, t in enumerate(texts)]
    chunks = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50).split_documents(docs)
    store = FAISS.from_documents(chunks, get_embeddings())
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    store.save_local(out_dir)  # ← 여기까지가 인덱싱. 서비스와 분리!


_STORES: dict[str, object] = {}  # 서비스: out_dir별 로드 1회 캐시


def search(query: str, out_dir: str, k: int = 3):
    """[서비스: 로드 1회] load_local 후 검색만. 거리(distance) 오름차순.

    out_dir별로 캐시한다(전역 단일 캐시는 다른 인덱스를 잘못 검색하는 버그가 된다).
    """
    from langchain_community.vectorstores import FAISS

    if out_dir not in _STORES:
        # allow_dangerous_deserialization: 자체 생성한 인덱스만 로드한다는 전제
        _STORES[out_dir] = FAISS.load_local(
            out_dir, get_embeddings(), allow_dangerous_deserialization=True
        )
    pairs = _STORES[out_dir].similarity_search_with_score(query, k=k)
    # score는 '거리'다(작을수록 유사) — 필드명을 distance로 두는 게 안전
    return [{"text": d.page_content, "source": d.metadata.get("source"), "distance": float(s)}
            for d, s in pairs]


if __name__ == "__main__":
    import tempfile

    tmp = tempfile.mkdtemp()
    build_index([
        "환불은 구매 후 7일 이내에 가능하며 전액 환불됩니다.",
        "제주 지역 반품 왕복 배송비는 10,000원입니다.",
        "로봇청소기 흡입력은 4,000Pa입니다.",
    ], tmp)
    for r in search("환불 며칠 이내 가능한가요?", tmp):
        print(round(r["distance"], 3), r["source"], "|", r["text"][:20])
    # 가장 관련된 문서가 가장 작은 distance로 1위에 온다
