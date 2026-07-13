"""프로젝트 공통 설정과 유틸리티 함수 모음입니다."""  # 이 파일의 목적을 설명하는 모듈 문서 문자열입니다.

from __future__ import annotations  # 타입 힌트에서 자기 자신 또는 나중에 정의될 타입을 안전하게 사용할 수 있게 합니다.

import hashlib  # 문자열을 안정적인 숫자 벡터로 바꾸기 위해 해시 함수를 사용합니다.
import math  # 벡터 정규화 계산에서 제곱근을 사용하기 위해 math 모듈을 불러옵니다.
import os  # 환경 변수와 파일 경로 처리를 위해 os 모듈을 불러옵니다.
from pathlib import Path  # 운영체제별 경로 차이를 줄이기 위해 Path 객체를 사용합니다.
from typing import Iterable, List, Sequence  # 함수 인자와 반환값을 명확히 표시하기 위해 타입 힌트를 불러옵니다.

from dotenv import load_dotenv  # .env 파일의 설정값을 환경 변수로 읽기 위해 python-dotenv를 사용합니다.
from langchain_core.documents import Document  # LangChain 벡터스토어에 넣을 표준 문서 객체입니다.
from langchain_core.embeddings import Embeddings  # 사용자 정의 임베딩 클래스를 만들기 위한 기본 인터페이스입니다.
from langchain_text_splitters import RecursiveCharacterTextSplitter  # 긴 문서를 작은 청크로 나누는 LangChain 분할기입니다.

load_dotenv()  # 프로젝트 루트의 .env 파일이 있으면 값을 읽어 환경 변수로 등록합니다.

PROJECT_ROOT = Path(__file__).resolve().parents[1]  # 현재 파일 기준으로 프로젝트 루트 폴더를 계산합니다.
DATA_DIR = PROJECT_ROOT / "data"  # 데이터 파일을 저장하는 data 폴더 경로입니다.
DOCS_DIR = DATA_DIR / "docs"  # 원본 문서 TXT/PDF 파일을 저장하는 docs 폴더 경로입니다.
INDEX_DIR = DATA_DIR / "indexes"  # FAISS/Chroma 인덱스를 저장하는 indexes 폴더 경로입니다.
FAISS_DIR = INDEX_DIR / "faiss_index"  # FAISS 인덱스를 저장할 폴더 경로입니다.
CHROMA_DIR = INDEX_DIR / "chroma_db"  # Chroma 인덱스를 저장할 폴더 경로입니다.
MEMBERSHIP_FAISS_DIR = DATA_DIR / "faiss_index" / "membership"  # 실습문제 전용 FAISS 인덱스(멤버십) 저장 경로입니다.

LOCAL_EMBEDDING_DIM = int(os.getenv("LOCAL_EMBEDDING_DIM", "256"))  # 로컬 해시 임베딩의 벡터 차원 수를 환경 변수에서 읽습니다.
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))  # 문서를 자를 청크 크기를 환경 변수에서 읽습니다.
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))  # 청크 사이에 겹칠 글자 수를 환경 변수에서 읽습니다.
EMBEDDING_BACKEND = os.getenv("EMBEDDING_BACKEND", "local").strip().lower()  # 사용할 임베딩 방식을 local 또는 google로 선택합니다.


class LocalHashEmbeddings(Embeddings):  # 외부 API 없이 실습할 수 있도록 만든 간단한 로컬 임베딩 클래스입니다.
    """문자열을 고정 길이 벡터로 바꾸는 실습용 임베딩입니다."""  # 클래스의 학습 목적을 설명합니다.

    def __init__(self, dim: int = LOCAL_EMBEDDING_DIM) -> None:  # 임베딩 차원을 입력받아 객체를 초기화합니다.
        self.dim = dim  # 이후 모든 문장을 같은 길이의 벡터로 만들기 위해 차원을 저장합니다.

    def _tokenize(self, text: str) -> List[str]:  # 문장을 간단한 토큰 리스트로 나누는 내부 함수입니다.
        normalized = text.lower().replace("\n", " ")  # 대소문자 차이를 줄이고 줄바꿈을 공백으로 바꿉니다.
        tokens = [token.strip() for token in normalized.split(" ") if token.strip()]  # 공백 기준으로 나누고 빈 토큰을 제거합니다.
        if tokens:  # 토큰이 하나라도 있으면 그대로 사용합니다.
            return tokens  # 정리된 토큰 리스트를 반환합니다.
        return [normalized] if normalized else ["empty"]  # 공백 문장도 에러가 나지 않도록 기본 토큰을 반환합니다.

    def _hash_token(self, token: str) -> int:  # 토큰을 안정적인 정수 인덱스로 바꾸는 내부 함수입니다.
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()  # 토큰 문자열을 SHA-256 해시 문자열로 변환합니다.
        return int(digest, 16) % self.dim  # 해시 값을 벡터 차원 범위 안의 인덱스로 변환합니다.

    def _embed_one(self, text: str) -> List[float]:  # 문장 하나를 벡터 하나로 변환하는 내부 함수입니다.
        vector = [0.0] * self.dim  # 지정한 차원 수만큼 0으로 채운 벡터를 만듭니다.
        for token in self._tokenize(text):  # 문장에서 추출한 각 토큰을 순회합니다.
            index = self._hash_token(token)  # 토큰이 들어갈 벡터 위치를 해시로 계산합니다.
            vector[index] += 1.0  # 해당 위치의 값을 1 증가시켜 토큰 빈도를 반영합니다.
        norm = math.sqrt(sum(value * value for value in vector))  # 벡터 길이를 계산해 정규화에 사용합니다.
        if norm == 0.0:  # 모든 값이 0이면 나눗셈 오류를 방지합니다.
            return vector  # 0 벡터를 그대로 반환합니다.
        return [value / norm for value in vector]  # 벡터 길이를 1로 맞춰 유사도 계산이 안정되게 합니다.

    def embed_documents(self, texts: List[str]) -> List[List[float]]:  # 여러 문서를 한 번에 임베딩하는 LangChain 표준 메서드입니다.
        return [self._embed_one(text) for text in texts]  # 각 문장을 벡터로 변환해 리스트로 반환합니다.

    def embed_query(self, text: str) -> List[float]:  # 질문 문장 하나를 임베딩하는 LangChain 표준 메서드입니다.
        return self._embed_one(text)  # 질문 하나를 고정 길이 벡터로 변환해 반환합니다.


def ensure_directories() -> None:  # 프로젝트 실행에 필요한 폴더들을 자동으로 만드는 함수입니다.
    DOCS_DIR.mkdir(parents=True, exist_ok=True)  # 문서 폴더가 없으면 생성합니다.
    FAISS_DIR.mkdir(parents=True, exist_ok=True)  # FAISS 인덱스 폴더가 없으면 생성합니다.
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)  # Chroma 인덱스 폴더가 없으면 생성합니다.


def get_embeddings() -> Embeddings:  # 설정값에 따라 임베딩 객체를 반환하는 함수입니다.
    if EMBEDDING_BACKEND == "google":  # 실제 Google Gemini 임베딩을 사용하도록 설정한 경우입니다.
        from langchain_google_genai import GoogleGenerativeAIEmbeddings  # Google 임베딩 클래스를 필요할 때만 불러옵니다.
        return GoogleGenerativeAIEmbeddings(model=os.getenv("GOOGLE_EMBEDDING_MODEL", "models/text-embedding-004"))  # Google 임베딩 객체를 반환합니다.
    return LocalHashEmbeddings(dim=LOCAL_EMBEDDING_DIM)  # 기본값은 API 키 없이 동작하는 로컬 해시 임베딩입니다.


def get_genai_embeddings() -> Embeddings:  # 실습문제 전용으로 Google Gemini 임베딩을 강제로 반환하는 함수입니다.
    from langchain_google_genai import GoogleGenerativeAIEmbeddings  # Google 임베딩 클래스를 필요할 때만 불러옵니다.
    if not os.getenv("GOOGLE_API_KEY"):  # 실습에 필요한 API 키가 없으면 명확한 오류로 안내합니다.
        raise RuntimeError("GOOGLE_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")  # 키 누락 시 원인을 알려 주는 예외입니다.
    model = os.getenv("GOOGLE_EMBEDDING_MODEL", "models/text-embedding-004")  # 사용할 Google 임베딩 모델명을 읽습니다.
    return GoogleGenerativeAIEmbeddings(model=model)  # .env의 EMBEDDING_BACKEND 값과 무관하게 Google 임베딩을 반환합니다.


def list_document_files(extension: str = ".txt") -> List[str]:  # docs 폴더에서 특정 확장자의 문서 파일명을 가져오는 함수입니다.
    ensure_directories()  # 폴더가 없는 상태에서도 안전하게 실행되도록 먼저 폴더를 생성합니다.
    return sorted(path.name for path in DOCS_DIR.glob(f"*{extension}"))  # 확장자에 맞는 파일명을 정렬해서 반환합니다.


def read_text_file(path: Path) -> str:  # UTF-8 텍스트 파일을 읽는 함수입니다.
    return path.read_text(encoding="utf-8")  # 파일 내용을 문자열로 반환합니다.


def load_txt_documents(filenames: Sequence[str]) -> List[Document]:  # 여러 TXT 파일을 LangChain Document 리스트로 로드합니다.
    docs: List[Document] = []  # 읽어 온 문서 객체를 담을 빈 리스트를 만듭니다.
    for filename in filenames:  # 전달받은 파일명을 하나씩 처리합니다.
        path = DOCS_DIR / filename  # docs 폴더 기준의 전체 파일 경로를 만듭니다.
        if not path.exists():  # 파일이 없으면 사용자에게 명확한 오류를 보여 줍니다.
            raise FileNotFoundError(f"문서 파일이 없습니다: {path}")  # 없는 파일 경로를 포함해 예외를 발생시킵니다.
        text = read_text_file(path)  # 텍스트 파일 내용을 읽습니다.
        docs.append(Document(page_content=text, metadata={"source": filename, "page": 0}))  # 내용과 출처 메타데이터를 가진 문서 객체를 추가합니다.
    return docs  # 전체 문서 객체 리스트를 반환합니다.


def load_pdf_documents(filenames: Sequence[str]) -> List[Document]:  # 여러 PDF 파일을 LangChain Document 리스트로 로드합니다.
    from langchain_community.document_loaders import PyPDFLoader  # PDF 로더는 필요할 때만 불러와 의존성을 명확히 합니다.
    docs: List[Document] = []  # PDF 페이지 문서들을 담을 빈 리스트를 만듭니다.
    for filename in filenames:  # 전달받은 PDF 파일명을 하나씩 처리합니다.
        path = DOCS_DIR / filename  # docs 폴더 기준의 PDF 전체 경로를 만듭니다.
        if not path.exists():  # PDF 파일이 없으면 명확한 오류를 발생시킵니다.
            raise FileNotFoundError(f"PDF 파일이 없습니다: {path}")  # 없는 파일 경로를 포함해 예외를 발생시킵니다.
        pages = PyPDFLoader(str(path)).load()  # PDF의 각 페이지를 Document 객체로 로드합니다.
        for page in pages:  # 로드된 각 페이지 문서를 순회합니다.
            page.metadata["source"] = filename  # 필터링이 쉽도록 전체 경로 대신 파일명만 source로 저장합니다.
        docs.extend(pages)  # 현재 PDF의 페이지 문서들을 전체 리스트에 추가합니다.
    return docs  # 전체 PDF 페이지 문서 리스트를 반환합니다.


def load_documents(filenames: Sequence[str]) -> List[Document]:  # TXT와 PDF를 확장자에 따라 자동 로드하는 함수입니다.
    if not filenames:  # 파일 목록이 비어 있으면 오류를 명확하게 알려 줍니다.
        raise ValueError("로드할 파일명이 비어 있습니다.")  # 잘못된 입력을 설명하는 예외를 발생시킵니다.
    if all(name.lower().endswith(".pdf") for name in filenames):  # 모든 파일이 PDF인지 확인합니다.
        return load_pdf_documents(filenames)  # PDF 전용 로더를 사용해 문서를 반환합니다.
    if all(name.lower().endswith(".txt") for name in filenames):  # 모든 파일이 TXT인지 확인합니다.
        return load_txt_documents(filenames)  # TXT 전용 로더를 사용해 문서를 반환합니다.
    raise ValueError("TXT와 PDF를 한 번에 섞지 말고 같은 확장자끼리 실행하세요.")  # 혼합 확장자 입력을 방지합니다.


def chunk_documents(documents: Sequence[Document]) -> List[Document]:  # 긴 문서를 검색용 청크로 나누는 함수입니다.
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)  # 청크 크기와 겹침 크기를 적용해 분할기를 만듭니다.
    return splitter.split_documents(list(documents))  # Document 리스트를 작은 청크 Document 리스트로 변환합니다.


def load_and_chunk(filenames: Sequence[str]) -> List[Document]:  # 파일 로드와 청킹을 한 번에 수행하는 편의 함수입니다.
    documents = load_documents(filenames)  # 파일 목록을 Document 리스트로 로드합니다.
    chunks = chunk_documents(documents)  # 로드한 문서를 청크 단위로 분할합니다.
    return chunks  # 검색 인덱스에 넣을 청크 리스트를 반환합니다.


def print_documents(title: str, docs: Sequence[Document], max_chars: int = 160) -> None:  # 검색 결과를 보기 좋게 출력하는 함수입니다.
    print(f"\n[{title}]")  # 결과 묶음의 제목을 출력합니다.
    if not docs:  # 검색 결과가 없을 때 안내 메시지를 출력합니다.
        print("검색 결과가 없습니다.")  # 빈 결과임을 사용자에게 알려 줍니다.
        return  # 더 이상 출력할 문서가 없으므로 함수를 종료합니다.
    for index, doc in enumerate(docs, start=1):  # 결과 문서를 1번부터 번호를 붙여 순회합니다.
        source = doc.metadata.get("source", "?")  # 문서 출처 파일명을 가져옵니다.
        page = doc.metadata.get("page", "?")  # 문서 페이지 정보를 가져옵니다.
        content = doc.page_content.replace("\n", " ")[:max_chars]  # 줄바꿈을 공백으로 바꾸고 앞부분만 잘라 표시합니다.
        print(f"{index}. 출처={source}, page={page}")  # 결과 번호와 출처 정보를 출력합니다.
        print(f"   {content}...")  # 청크 내용 일부를 출력합니다.


def print_scored_documents(title: str, scored_docs: Iterable[tuple[Document, float]], max_chars: int = 160) -> None:  # 점수 포함 검색 결과를 출력합니다.
    print(f"\n[{title}]")  # 결과 묶음의 제목을 출력합니다.
    for index, (doc, score) in enumerate(scored_docs, start=1):  # 문서와 점수를 1번부터 번호를 붙여 순회합니다.
        source = doc.metadata.get("source", "?")  # 문서 출처 파일명을 가져옵니다.
        content = doc.page_content.replace("\n", " ")[:max_chars]  # 줄바꿈을 제거하고 내용 앞부분만 표시합니다.
        print(f"{index}. 거리={score:.4f}, 출처={source}")  # FAISS 거리 점수와 출처를 출력합니다.
        print(f"   {content}...")  # 검색된 문서 청크 일부를 출력합니다.
