# -*- coding: utf-8 -*-
"""RAG QA 서비스 모듈.

이 모듈은 정책 PDF를 로드하고, 청킹하고, 임베딩하여 메모리 검색기를 만든 뒤,
검색 결과만 근거로 답변하고 출처를 함께 반환하는 기능을 제공합니다.

Windows에서 PyTorch와 FAISS가 서로 다른 OpenMP DLL을 동시에 로드하는 문제를
방지하기 위해 FAISS 대신 LangChain의 InMemoryVectorStore를 사용합니다.
"""

# 운영체제와 무관하게 파일명만 추출하기 위해 Path 클래스를 가져옵니다.
from pathlib import Path

# 타입 힌트에 사용할 Any와 Iterable을 가져옵니다.
from typing import Any, Iterable

# PyTorch 텐서 연산과 코사인 유사도 계산을 위해 torch를 가져옵니다.
import torch

# 제공된 공통 모듈에서 문서 경로, 채팅 모델, 임베딩 모델 생성 함수를 가져옵니다.
from common import DOCS, get_chat, get_embeddings

# PDF 파일을 페이지 단위 Document 객체로 읽기 위해 PyPDFLoader를 가져옵니다.
from langchain_community.document_loaders import PyPDFLoader

# 별도 네이티브 DLL 없이 동작하는 LangChain 메모리 벡터 저장소를 가져옵니다.
# FAISS를 사용하지 않으므로 libomp140.x86_64.dll과 libiomp5md.dll 충돌을 피할 수 있습니다.
from langchain_core.vectorstores import InMemoryVectorStore

# LLM 응답 객체에서 문자열만 추출하기 위해 StrOutputParser를 가져옵니다.
from langchain_core.output_parsers import StrOutputParser

# 환각 억제용 프롬프트 템플릿을 만들기 위해 ChatPromptTemplate을 가져옵니다.
from langchain_core.prompts import ChatPromptTemplate

# LCEL에서 입력 질문을 그대로 통과시키기 위해 RunnablePassthrough를 가져옵니다.
from langchain_core.runnables import RunnablePassthrough

# 긴 문서를 의미 단위 청크로 나누기 위해 RecursiveCharacterTextSplitter를 가져옵니다.
from langchain_text_splitters import RecursiveCharacterTextSplitter


# 정책 문서에 없는 내용은 추측하지 않도록 명시한 공통 프롬프트를 정의합니다.
PROMPT = ChatPromptTemplate.from_template(
    "너는 쇼핑몰 정책 문서를 기반으로 답하는 CS 상담원이다.\n"
    "아래 [문서] 내용만 근거로 한국어로 정확하고 간결하게 답하라.\n"
    "문서에 없는 내용은 추측하거나 일반 지식을 섞지 말고 "
    "'제공된 문서에서 찾을 수 없습니다.'라고 답하라.\n"
    "답변에 근거가 되는 핵심 조건이나 기간이 있으면 빠뜨리지 말라.\n\n"
    "[문서]\n{context}\n\n"
    "[질문]\n{question}\n\n"
    "[답변]"
)


# 검색기와 LLM을 최초 한 번만 만들어 재사용하기 위한 전역 캐시를 선언합니다.
_RETRIEVER_CACHE: dict[tuple[str, int], Any] = {}

# 채팅 모델을 제공자별로 최초 한 번만 만들어 재사용하기 위한 전역 캐시를 선언합니다.
_LLM_CACHE: dict[str, Any] = {}


def load_policy_documents() -> list[Any]:
    """docs 폴더의 모든 PDF를 페이지 단위 Document 리스트로 로드합니다."""

    # 파일명이 달라져도 실행되도록 특정 이름을 하드코딩하지 않고 모든 PDF를 찾습니다.
    pdf_paths = sorted(DOCS.glob("*.pdf"))

    # PDF가 하나도 없으면 설정 문제를 바로 확인할 수 있도록 예외를 발생시킵니다.
    if not pdf_paths:
        raise FileNotFoundError(f"PDF 문서를 찾을 수 없습니다: {DOCS}")

    # 여러 PDF에서 읽은 Document 객체를 누적할 빈 리스트를 만듭니다.
    documents: list[Any] = []

    # docs 폴더에서 찾은 각 PDF 파일을 차례로 처리합니다.
    for pdf_path in pdf_paths:
        # 현재 PDF를 페이지 단위 Document 객체로 읽는 로더를 생성합니다.
        loader = PyPDFLoader(str(pdf_path))

        # 현재 PDF의 모든 페이지를 읽어 전체 문서 리스트 뒤에 추가합니다.
        loaded_pages = loader.load()

        # 일부 PDF에서 source metadata가 누락되더라도 출처가 유지되도록 보정합니다.
        for page in loaded_pages:
            page.metadata.setdefault("source", str(pdf_path))

        # 현재 PDF에서 읽은 페이지들을 전체 문서 리스트에 추가합니다.
        documents.extend(loaded_pages)

    # docs 폴더에서 읽은 모든 페이지 Document를 반환합니다.
    return documents


def split_documents(
    documents: list[Any],
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[Any]:
    """페이지 Document를 검색에 적합한 작은 청크로 나눕니다."""

    # 청크 크기와 겹침 크기를 검증하여 잘못된 설정을 조기에 차단합니다.
    if chunk_size <= 0:
        raise ValueError("chunk_size는 1 이상이어야 합니다.")

    # 겹침은 음수가 될 수 없고 청크 크기보다 작아야 합니다.
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap은 0 이상이고 chunk_size보다 작아야 합니다.")

    # 단락, 줄바꿈, 공백 순으로 가능한 자연스러운 경계를 찾는 분할기를 생성합니다.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    # 원본 metadata를 보존하면서 문서들을 청크 단위로 분할합니다.
    chunks = splitter.split_documents(documents)

    # 각 청크에 화면 표시용 청크 번호를 추가합니다.
    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = index

    # 분할이 완료된 청크 리스트를 반환합니다.
    return chunks


def build_vector_store(provider: str = "gemini") -> InMemoryVectorStore:
    """정책 문서를 임베딩하여 메모리 벡터 저장소를 생성합니다."""

    # PDF 문서를 페이지 단위로 읽습니다.
    documents = load_policy_documents()

    # 읽은 문서를 기본 설정인 500자, 50자 겹침으로 청킹합니다.
    chunks = split_documents(documents)

    # common.py를 통해 선택한 제공자의 임베딩 모델을 생성합니다.
    embeddings = get_embeddings(provider)

    # FAISS 대신 순수 Python 중심의 메모리 벡터 저장소를 생성합니다.
    vector_store = InMemoryVectorStore(embedding=embeddings)

    # 청크 본문과 metadata를 임베딩하여 메모리 벡터 저장소에 추가합니다.
    vector_store.add_documents(documents=chunks)

    # 생성한 벡터 저장소를 반환합니다.
    return vector_store


def get_retriever(provider: str = "gemini", k: int = 4) -> Any:
    """선택한 제공자와 k값에 맞는 검색기를 캐시하여 반환합니다."""

    # 검색 개수는 최소 1개 이상이어야 합니다.
    if k <= 0:
        raise ValueError("k는 1 이상이어야 합니다.")

    # 제공자와 k값을 조합해 캐시 키를 만듭니다.
    cache_key = (provider, k)

    # 아직 해당 검색기가 만들어지지 않았다면 새로 생성합니다.
    if cache_key not in _RETRIEVER_CACHE:
        # 선택한 임베딩 제공자로 벡터 저장소를 생성합니다.
        vector_store = build_vector_store(provider)

        # 벡터 저장소를 질문 입력형 검색기로 변환하고 상위 k개를 반환하도록 설정합니다.
        _RETRIEVER_CACHE[cache_key] = vector_store.as_retriever(
            search_kwargs={"k": k}
        )

    # 캐시에 보관된 검색기를 반환합니다.
    return _RETRIEVER_CACHE[cache_key]


def get_llm(provider: str = "gemini") -> Any:
    """temperature=0인 채팅 모델을 제공자별로 캐시하여 반환합니다."""

    # 아직 해당 제공자의 채팅 모델이 없다면 새로 생성합니다.
    if provider not in _LLM_CACHE:
        # 사실 기반 답변의 일관성을 위해 temperature를 0으로 설정합니다.
        _LLM_CACHE[provider] = get_chat(provider=provider, temperature=0.0)

    # 캐시에 저장된 채팅 모델을 반환합니다.
    return _LLM_CACHE[provider]


def format_docs(documents: Iterable[Any]) -> str:
    """검색된 Document들의 본문과 간단한 출처를 하나의 context 문자열로 합칩니다."""

    # 문서별로 정리된 문자열을 저장할 빈 리스트를 만듭니다.
    blocks: list[str] = []

    # 검색된 각 문서를 차례로 처리합니다.
    for index, document in enumerate(documents, start=1):
        # metadata의 전체 경로에서 파일명만 안전하게 추출합니다.
        source = Path(str(document.metadata.get("source", "알 수 없음"))).name

        # PyPDFLoader의 페이지 번호는 0부터 시작하므로 사용자 표시용으로 1을 더합니다.
        raw_page = document.metadata.get("page")
        display_page = raw_page + 1 if isinstance(raw_page, int) else "?"

        # 번호, 파일명, 페이지, 본문을 하나의 근거 블록으로 구성합니다.
        block = (
            f"[근거 {index} | {source} | {display_page}페이지]\n"
            f"{document.page_content.strip()}"
        )

        # 완성한 근거 블록을 리스트에 추가합니다.
        blocks.append(block)

    # 각 근거 블록 사이를 빈 줄로 구분해 하나의 context 문자열로 반환합니다.
    return "\n\n".join(blocks)


def extract_sources(documents: Iterable[Any]) -> list[dict[str, Any]]:
    """검색 문서의 파일명과 페이지를 중복 없이 추출합니다."""

    # 최종 출처 목록을 저장할 빈 리스트를 만듭니다.
    sources: list[dict[str, Any]] = []

    # 이미 추가한 출처를 빠르게 확인하기 위한 집합을 만듭니다.
    seen: set[tuple[str, Any]] = set()

    # 검색된 각 문서를 차례로 처리합니다.
    for document in documents:
        # 전체 경로가 아닌 파일명만 추출합니다.
        source = Path(str(document.metadata.get("source", "알 수 없음"))).name

        # 내부 페이지 번호를 가져옵니다.
        raw_page = document.metadata.get("page")

        # 화면과 JSON 응답에서는 사람이 읽는 1부터 시작하는 페이지 번호로 바꿉니다.
        display_page = raw_page + 1 if isinstance(raw_page, int) else None

        # 파일명과 페이지 번호를 중복 판단 키로 사용합니다.
        key = (source, display_page)

        # 아직 추가하지 않은 출처만 결과에 넣습니다.
        if key not in seen:
            seen.add(key)
            sources.append({"source": source, "page": display_page})

    # 중복이 제거된 출처 리스트를 반환합니다.
    return sources


def create_lcel_chain(provider: str = "gemini", k: int = 4) -> Any:
    """검색→프롬프트→LLM→문자열 변환을 연결한 LCEL 체인을 생성합니다."""

    # 선택한 제공자와 k값으로 검색기를 가져옵니다.
    retriever = get_retriever(provider=provider, k=k)

    # 선택한 제공자의 채팅 모델을 가져옵니다.
    llm = get_llm(provider=provider)

    # 질문 하나에서 context와 question 두 입력을 만드는 LCEL 체인을 구성합니다.
    chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough(),
        }
        | PROMPT
        | llm
        | StrOutputParser()
    )

    # 완성한 LCEL 체인을 반환합니다.
    return chain


def answer(question: str, provider: str = "gemini", k: int = 4) -> dict[str, Any]:
    """질문에 대해 문서 근거 답변과 출처를 함께 반환합니다."""

    # 공백만 있는 질문은 API 호출 전에 차단합니다.
    if not question or not question.strip():
        raise ValueError("질문을 한 글자 이상 입력해야 합니다.")

    # 출처를 보존하기 위해 검색을 체인 밖에서 먼저 실행합니다.
    retriever = get_retriever(provider=provider, k=k)

    # 질문과 의미가 가까운 상위 k개 청크를 검색합니다.
    documents = retriever.invoke(question.strip())

    # 검색된 청크를 LLM 프롬프트에 넣을 하나의 문자열로 합칩니다.
    context = format_docs(documents)

    # 선택한 제공자의 채팅 모델을 가져옵니다.
    llm = get_llm(provider=provider)

    # 프롬프트, LLM, 문자열 파서를 연결한 간단한 생성 체인을 만듭니다.
    generation_chain = PROMPT | llm | StrOutputParser()

    # 검색 문서와 원본 질문을 넣어 근거 제한 답변을 생성합니다.
    response_text = generation_chain.invoke(
        {"context": context, "question": question.strip()}
    )

    # 답변 문자열과 중복 제거된 출처를 딕셔너리로 묶어 반환합니다.
    return {
        "answer": response_text,
        "sources": extract_sources(documents),
    }


def compare_k(question: str, provider: str = "gemini", values: tuple[int, ...] = (2, 4, 6)) -> dict[int, list[Any]]:
    """여러 k값으로 검색한 청크를 비교할 수 있도록 딕셔너리로 반환합니다."""

    # k값별 검색 결과를 저장할 빈 딕셔너리를 만듭니다.
    result: dict[int, list[Any]] = {}

    # 지정한 각 k값으로 검색을 반복합니다.
    for k in values:
        # 현재 k값에 맞는 검색기를 가져옵니다.
        retriever = get_retriever(provider=provider, k=k)

        # 현재 질문에 대한 검색 결과를 저장합니다.
        result[k] = retriever.invoke(question)

    # k값별 검색 결과 딕셔너리를 반환합니다.
    return result


def torch_rerank(question: str, documents: list[Any], provider: str = "gemini", top_n: int = 2) -> list[tuple[float, Any]]:
    """PyTorch 코사인 유사도로 후보 청크를 다시 정렬합니다."""

    # 반환할 문서 수가 1 이상인지 검증합니다.
    if top_n <= 0:
        raise ValueError("top_n은 1 이상이어야 합니다.")

    # 선택한 제공자의 임베딩 모델을 가져옵니다.
    embeddings = get_embeddings(provider)

    # 사용자 질문 한 개를 검색용 벡터로 변환합니다.
    question_vector = embeddings.embed_query(question)

    # 후보 청크 본문을 리스트로 추출합니다.
    document_texts = [document.page_content for document in documents]

    # 여러 후보 청크를 한 번의 배치 호출로 임베딩합니다.
    document_vectors = embeddings.embed_documents(document_texts)

    # 질문 벡터를 float32 PyTorch 텐서로 변환하고 배치 차원을 추가합니다.
    q_tensor = torch.tensor(question_vector, dtype=torch.float32).unsqueeze(0)

    # 문서 벡터 목록을 float32 PyTorch 행렬로 변환합니다.
    d_tensor = torch.tensor(document_vectors, dtype=torch.float32)

    # 질문 벡터를 L2 정규화하여 방향 비교가 가능하도록 만듭니다.
    q_normalized = torch.nn.functional.normalize(q_tensor, p=2, dim=1)

    # 모든 문서 벡터도 행 단위로 L2 정규화합니다.
    d_normalized = torch.nn.functional.normalize(d_tensor, p=2, dim=1)

    # 정규화된 질문과 문서 행렬의 내적으로 코사인 유사도를 한 번에 계산합니다.
    scores = torch.matmul(d_normalized, q_normalized.transpose(0, 1)).squeeze(1)

    # 점수를 Python 실수와 Document 쌍으로 묶습니다.
    scored_documents = [
        (float(score.item()), document)
        for score, document in zip(scores, documents)
    ]

    # 코사인 유사도가 높은 문서가 앞에 오도록 내림차순 정렬합니다.
    scored_documents.sort(key=lambda item: item[0], reverse=True)

    # 요청한 상위 top_n개만 반환합니다.
    return scored_documents[:top_n]


def _parse_score(raw_text: str) -> int:
    """LLM이 반환한 문자열에서 0~10 범위 정수를 안전하게 추출합니다."""

    # 문자열 안의 숫자만 차례로 모읍니다.
    digits = "".join(character for character in raw_text if character.isdigit())

    # 숫자가 하나도 없다면 가장 낮은 관련도인 0점을 반환합니다.
    if not digits:
        return 0

    # 추출한 숫자를 정수로 바꿉니다.
    score = int(digits)

    # 점수가 0보다 작거나 10보다 커지지 않도록 범위를 제한합니다.
    return max(0, min(score, 10))


def llm_rerank(
    question: str,
    documents: list[Any],
    provider: str = "gemini",
    top_n: int = 2,
) -> list[tuple[int, Any]]:
    """LLM이 후보 청크의 질문 관련도를 0~10점으로 평가해 재정렬합니다."""

    # 반환할 문서 수가 1 이상인지 검증합니다.
    if top_n <= 0:
        raise ValueError("top_n은 1 이상이어야 합니다.")

    # 사실 판단의 일관성을 위해 temperature=0인 채팅 모델을 가져옵니다.
    llm = get_llm(provider)

    # 점수와 문서 쌍을 저장할 빈 리스트를 만듭니다.
    scored_documents: list[tuple[int, Any]] = []

    # 각 후보 문서를 개별적으로 평가합니다.
    for document in documents:
        # 과도한 토큰 사용을 막기 위해 청크 앞부분 700자까지만 평가에 사용합니다.
        content = document.page_content[:700]

        # LLM이 설명 없이 정수 하나만 반환하도록 매우 제한적인 채점 프롬프트를 만듭니다.
        scoring_prompt = (
            "다음 [문서조각]이 [질문]에 직접 답하는 데 얼마나 관련 있는지 "
            "0부터 10까지의 정수 하나로만 답하라. 설명이나 기호를 출력하지 말라.\n\n"
            f"[질문]\n{question}\n\n"
            f"[문서조각]\n{content}\n\n"
            "[점수]"
        )

        # 채팅 모델로 관련도 점수를 요청합니다.
        response = llm.invoke(scoring_prompt)

        # 모델 응답 객체의 content 문자열을 안전하게 가져옵니다.
        raw_text = str(getattr(response, "content", response))

        # 문자열을 0~10 범위 정수로 변환합니다.
        score = _parse_score(raw_text)

        # 계산한 점수와 원본 문서를 함께 저장합니다.
        scored_documents.append((score, document))

    # 점수가 높은 문서가 앞에 오도록 내림차순 정렬합니다.
    scored_documents.sort(key=lambda item: item[0], reverse=True)

    # 상위 top_n개 결과만 반환합니다.
    return scored_documents[:top_n]
