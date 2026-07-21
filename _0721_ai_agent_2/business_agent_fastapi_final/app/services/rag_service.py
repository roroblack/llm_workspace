# -*- coding: utf-8 -*-
"""PDF와 주요 CSV를 근거로 검색하는 RAG 서비스입니다."""

# 여러 종류의 문서를 동일한 목록으로 다루기 위해 Any 타입을 가져옵니다.
from typing import Any
# PDF와 CSV 경로를 가져옵니다.
from app.core.settings import DATA_DIR, DOCS_DIR, RAG_TOP_K
# 공급자별 임베딩 모델을 만들기 위해 공통 함수를 가져옵니다.
from app.core.common import get_embeddings

# 공급자별 벡터 저장소를 메모리에 재사용하기 위한 캐시 딕셔너리를 생성합니다.
_VECTOR_CACHE: dict[str, Any] = {}


def _load_documents() -> list[Any]:
    """PDF와 핵심 CSV를 LangChain Document 목록으로 변환합니다."""
    # LangChain 표준 문서 객체를 지연 import합니다.
    from langchain_core.documents import Document
    # PDF 파일을 페이지 단위로 읽기 위해 PyPDFLoader를 지연 import합니다.
    from langchain_community.document_loaders import PyPDFLoader
    # 최종 문서 목록을 저장할 빈 리스트를 생성합니다.
    documents: list[Any] = []
    # docs 폴더의 모든 PDF를 순회합니다.
    for pdf_path in sorted(DOCS_DIR.glob("*.pdf")):
        # PDF의 각 페이지를 Document로 읽습니다.
        pages = PyPDFLoader(str(pdf_path)).load()
        # 각 페이지 메타데이터에 원본 파일명을 명시합니다.
        for page in pages:
            page.metadata["source"] = pdf_path.name
        # 페이지 문서를 전체 목록에 추가합니다.
        documents.extend(pages)
    # RAG 근거에 포함할 핵심 CSV 파일을 정의합니다.
    csv_names = ["monthly_sales.csv", "competitor_data.csv", "marketing_brief.csv", "products.csv", "reviews.csv"]
    # 각 CSV를 텍스트 문서로 변환합니다.
    for csv_name in csv_names:
        # CSV 전체 경로를 계산합니다.
        csv_path = DATA_DIR / csv_name
        # 파일이 없는 경우 해당 CSV를 건너뜁니다.
        if not csv_path.exists():
            continue
        # CSV 원문을 UTF-8로 읽습니다.
        text = csv_path.read_text(encoding="utf-8-sig")
        # 출처가 포함된 Document 객체를 목록에 추가합니다.
        documents.append(Document(page_content=text, metadata={"source": csv_name, "type": "csv"}))
    # 수집된 전체 문서를 반환합니다.
    return documents


def get_vector_store(provider: str) -> Any:
    """공급자별 임베딩을 사용하는 FAISS 벡터 저장소를 반환합니다."""
    # 이미 생성된 벡터 저장소가 있으면 재사용합니다.
    if provider in _VECTOR_CACHE:
        return _VECTOR_CACHE[provider]
    # 문서를 적절한 길이로 분할하기 위해 텍스트 분할기를 가져옵니다.
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    # 벡터 유사도 검색을 위해 FAISS 구현을 가져옵니다.
    from langchain_community.vectorstores import FAISS
    # PDF와 CSV 문서를 모두 읽습니다.
    documents = _load_documents()
    # 문서가 하나도 없으면 RAG를 만들 수 없으므로 오류를 발생시킵니다.
    if not documents:
        raise ValueError("RAG에 사용할 PDF 또는 CSV 문서가 없습니다.")
    # 문맥 보존과 검색 정확도를 고려한 분할기를 생성합니다.
    splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=150)
    # 모든 문서를 검색 가능한 작은 청크로 나눕니다.
    chunks = splitter.split_documents(documents)
    # 사용자가 선택한 공급자의 임베딩 모델을 생성합니다.
    embeddings = get_embeddings(provider=provider)
    # 문서 청크와 임베딩을 이용해 FAISS 인덱스를 생성합니다.
    vector_store = FAISS.from_documents(chunks, embeddings)
    # 다음 요청에서 재사용하도록 벡터 저장소를 캐시에 보관합니다.
    _VECTOR_CACHE[provider] = vector_store
    # 생성된 벡터 저장소를 반환합니다.
    return vector_store


def search_knowledge(query: str, provider: str, top_k: int = RAG_TOP_K) -> dict[str, object]:
    """질문과 유사한 근거 문서를 검색해 본문과 출처를 반환합니다."""
    # 공급자별 벡터 저장소를 가져옵니다.
    vector_store = get_vector_store(provider)
    # 질문과 유사한 상위 문서를 검색합니다.
    documents = vector_store.similarity_search(query, k=max(1, min(top_k, 10)))
    # 검색 결과를 API에서 사용하기 쉬운 딕셔너리 목록으로 변환합니다.
    sources = [{"source": doc.metadata.get("source", "unknown"), "page": doc.metadata.get("page"), "content": doc.page_content[:1200]} for doc in documents]
    # LLM 프롬프트에 넣을 근거 문자열을 번호와 함께 생성합니다.
    context = "\n\n".join(f"[근거 {index}] 출처={item['source']} 페이지={item['page']}\n{item['content']}" for index, item in enumerate(sources, start=1))
    # 근거 문자열과 구조화된 출처를 함께 반환합니다.
    return {"context": context, "sources": sources}


def reset_rag() -> None:
    """메모리에 저장된 모든 공급자별 벡터 인덱스를 초기화합니다."""
    # 캐시 딕셔너리의 모든 항목을 제거합니다.
    _VECTOR_CACHE.clear()
