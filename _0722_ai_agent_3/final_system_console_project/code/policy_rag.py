# -*- coding: utf-8 -*-
"""정책 PDF를 검색하는 RAG 도구를 생성하는 모듈입니다."""

# 공통 모듈에서 정책 문서 폴더와 임베딩 생성 함수를 가져옵니다.
from common import DOCS, get_embeddings
# 현재 선택된 OpenAI 또는 Gemini 공급자를 가져옵니다.
from app_context import get_provider


def list_policy_pdfs():
    """data/docs에 포함된 모든 PDF 경로를 정렬해 반환합니다."""
    # 파일명이 한글로 복원되지 않아도 확장자가 pdf이면 모두 정책 문서로 취급합니다.
    return sorted(DOCS.glob("*.pdf"))


def build_policy_tool(config: dict, logger):
    """모든 정책 PDF를 로드해 FAISS 검색기를 만들고 LangChain 도구로 감쌉니다."""
    # PDF를 페이지 단위 LangChain 문서로 읽기 위해 로더를 가져옵니다.
    from langchain_community.document_loaders import PyPDFLoader
    # 긴 페이지 텍스트를 검색 청크로 나누기 위해 분할기를 가져옵니다.
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    # 메모리 기반 벡터 검색 인덱스를 만들기 위해 FAISS를 가져옵니다.
    from langchain_community.vectorstores import FAISS
    # 완성된 retriever를 에이전트 도구로 변환하는 함수를 가져옵니다.
    from langchain_core.tools.retriever import create_retriever_tool

    # data/docs 아래의 모든 PDF 파일을 탐색합니다.
    pdf_files = list_policy_pdfs()
    # 정책 PDF가 없으면 RAG 구성이 불가능하므로 구체적인 오류를 발생시킵니다.
    if not pdf_files:
        raise FileNotFoundError(f"정책 PDF가 없습니다: {DOCS}")
    # 정책 인덱싱 시작 사실과 문서 수를 로그에 기록합니다.
    logger.info("정책 RAG 인덱싱 시작: PDF %s개", len(pdf_files))
    # 여러 PDF에서 읽은 페이지 문서를 누적할 빈 리스트를 준비합니다.
    documents = []
    # 발견된 모든 PDF 파일을 하나씩 순회합니다.
    for pdf_path in pdf_files:
        # 현재 읽는 PDF 파일명을 로그에 남겨 문제 발생 시 추적할 수 있게 합니다.
        logger.info("정책 PDF 로드: %s", pdf_path.name)
        # PDF의 모든 페이지를 LangChain Document 객체로 읽어 목록에 추가합니다.
        documents.extend(PyPDFLoader(str(pdf_path)).load())
    # config.yaml의 청크 크기와 중첩 크기를 사용하는 분할기를 생성합니다.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=int(config["rag"]["chunk_size"]),
        chunk_overlap=int(config["rag"]["chunk_overlap"]),
    )
    # 페이지 문서를 의미 검색에 적합한 작은 청크로 분할합니다.
    chunks = splitter.split_documents(documents)
    # 현재 사용자가 선택한 공급자의 임베딩 모델을 생성합니다.
    embeddings = get_embeddings(provider=get_provider())
    # 문서 청크를 임베딩하고 FAISS 벡터 인덱스를 메모리에 생성합니다.
    vector_store = FAISS.from_documents(chunks, embeddings)
    # 질문과 가까운 상위 k개 청크를 돌려주는 검색기를 생성합니다.
    retriever = vector_store.as_retriever(search_kwargs={"k": int(config["rag"]["top_k"])})
    # 최종 청크 개수를 로그에 기록합니다.
    logger.info("정책 RAG 인덱싱 완료: 청크 %s개", len(chunks))
    # 검색기를 policy_search라는 이름의 에이전트 도구로 감싸 반환합니다.
    return create_retriever_tool(
        retriever,
        "policy_search",
        "환불, 교환, 멤버십, 배송 등 쇼핑몰 정책 PDF에서 근거 문서를 검색한다.",
    )
