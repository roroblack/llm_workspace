# -*- coding: utf-8 -*-
"""정책 PDF를 임베딩하고 FAISS 검색기로 제공하는 RAG 서비스입니다."""

# threading.Lock은 동일 공급자의 인덱스를 여러 요청이 동시에 만들지 않도록 보호합니다.
from threading import Lock
# typing.Literal은 지원 공급자 값을 제한합니다.
from typing import Literal

# Document는 검색 결과 문서 타입을 명시할 때 사용합니다.
from langchain_core.documents import Document

# 공통 설정과 정책 문서 경로를 가져옵니다.
from app.core.settings import DOCS_DIR, get_settings
# 공급자별 임베딩 모델 생성 함수를 가져옵니다.
from app.services.llm_factory import create_embeddings

# _rag_lock은 인덱스 초기화 구간을 직렬화합니다.
_rag_lock = Lock()
# _vectorstores는 공급자별 FAISS 인덱스를 메모리에 캐시합니다.
_vectorstores: dict[str, object] = {}


# _build_vectorstore 함수는 정책 PDF 전체로 FAISS 인덱스를 만듭니다.
def _build_vectorstore(provider: Literal["openai", "gemini"]):
    """정책 PDF 로드, 청크 분할, 임베딩, FAISS 색인을 수행합니다."""
    # PDF 로더를 지연 import하여 데이터 도구만 사용할 때 초기화 비용을 줄입니다.
    from langchain_community.document_loaders import PyPDFLoader
    # FAISS 벡터 저장소 클래스를 가져옵니다.
    from langchain_community.vectorstores import FAISS
    # 긴 문서를 겹치는 청크로 나누는 분할기를 가져옵니다.
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    # 현재 RAG 설정값을 읽습니다.
    settings = get_settings()
    # docs 폴더의 모든 PDF를 파일명에 관계없이 찾습니다.
    pdf_files = sorted(DOCS_DIR.glob("*.pdf"))
    # 정책 PDF가 없으면 검색기를 만들 수 없으므로 오류를 발생시킵니다.
    if not pdf_files:
        # 정확한 확인 경로를 포함한 메시지를 제공합니다.
        raise FileNotFoundError(f"정책 PDF를 찾을 수 없습니다: {DOCS_DIR}")
    # 여러 PDF에서 읽은 페이지 문서를 저장할 리스트입니다.
    documents: list[Document] = []
    # 각 PDF를 순서대로 로드합니다.
    for pdf_file in pdf_files:
        # PyPDFLoader가 PDF 페이지를 LangChain Document 목록으로 변환합니다.
        loaded_pages = PyPDFLoader(str(pdf_file)).load()
        # 각 페이지 메타데이터에 원본 파일명을 추가합니다.
        for page in loaded_pages:
            # source_name은 답변 근거 표시에 사용됩니다.
            page.metadata["source_name"] = pdf_file.name
        # 로드한 페이지들을 전체 문서 목록에 추가합니다.
        documents.extend(loaded_pages)
    # 설정값으로 재귀 문자 분할기를 생성합니다.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
    )
    # 페이지 문서를 검색 가능한 크기의 청크로 나눕니다.
    chunks = splitter.split_documents(documents)
    # 선택한 공급자의 임베딩 모델을 생성합니다.
    embeddings = create_embeddings(provider)
    # 모든 청크를 벡터로 변환하고 메모리 FAISS 인덱스를 생성합니다.
    return FAISS.from_documents(chunks, embeddings)


# get_vectorstore 함수는 공급자별 인덱스를 한 번만 생성해 반환합니다.
def get_vectorstore(provider: Literal["openai", "gemini"]):
    """캐시된 FAISS 벡터 저장소를 반환합니다."""
    # 해당 공급자의 인덱스가 있으면 즉시 재사용합니다.
    if provider in _vectorstores:
        # 캐시된 인덱스를 반환합니다.
        return _vectorstores[provider]
    # 동시 최초 생성을 막기 위해 잠금을 획득합니다.
    with _rag_lock:
        # 대기 중 다른 요청이 생성했는지 다시 확인합니다.
        if provider not in _vectorstores:
            # 공급자별 인덱스를 생성해 캐시에 저장합니다.
            _vectorstores[provider] = _build_vectorstore(provider)
    # 최종 인덱스를 반환합니다.
    return _vectorstores[provider]


# search_policy 함수는 질문과 관련된 정책 문서를 검색합니다.
def search_policy(query: str, provider: Literal["openai", "gemini"]) -> str:
    """정책 PDF에서 관련 청크를 검색하고 출처와 함께 반환합니다."""
    # 공통 설정에서 top_k 값을 읽습니다.
    settings = get_settings()
    # 선택 공급자의 FAISS 인덱스를 가져옵니다.
    vectorstore = get_vectorstore(provider)
    # 유사도 검색으로 관련 문서 청크를 찾습니다.
    documents = vectorstore.similarity_search(query, k=settings.rag_top_k)
    # 결과가 없으면 정책 근거를 찾지 못했다고 반환합니다.
    if not documents:
        # 정책에 없는 내용을 생성하지 않도록 명시합니다.
        return "정책 문서에서 관련 근거를 찾지 못했습니다."
    # 검색 결과를 번호와 출처가 포함된 문자열로 변환합니다.
    sections: list[str] = []
    # 각 검색 결과를 순회합니다.
    for index, document in enumerate(documents, start=1):
        # 문서 메타데이터에서 원본 파일명을 읽습니다.
        source_name = document.metadata.get("source_name", document.metadata.get("source", "출처 미상"))
        # 페이지 번호가 있으면 사람이 읽는 1부터 시작하는 번호로 바꿉니다.
        page_number = int(document.metadata.get("page", 0)) + 1
        # 불필요한 줄바꿈을 정리한 본문을 만듭니다.
        content = " ".join(document.page_content.split())
        # 검색 순위, 출처, 페이지, 본문을 하나의 섹션으로 저장합니다.
        sections.append(f"[{index}] 출처={source_name}, 페이지={page_number}\n{content}")
    # 모든 근거 청크를 빈 줄로 구분하여 반환합니다.
    return "\n\n".join(sections)


# reset_rag_cache 함수는 모델 변경 또는 문서 수정 후 인덱스를 다시 만들 때 사용합니다.
def reset_rag_cache() -> None:
    """메모리에 캐시된 모든 FAISS 인덱스를 제거합니다."""
    # 공급자별 인덱스 딕셔너리를 비웁니다.
    _vectorstores.clear()
