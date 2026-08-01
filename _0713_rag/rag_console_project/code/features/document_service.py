# 문서 로드와 청킹 기능을 한곳에 모은 서비스 모듈입니다.
from pathlib import Path
from langchain_community.document_loaders import CSVLoader, PyPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from common import DATA, DOCS


def ensure_file(path: Path) -> Path:
    """실습 파일이 실제로 존재하는지 검사한 뒤 경로를 반환합니다."""
    if not path.exists():
        raise FileNotFoundError(f"실습 파일을 찾을 수 없습니다: {path}")
    return path


def load_pdf(file_name: str = "환불교환정책.pdf") -> list[Document]:
    """PDF를 페이지 단위 Document 목록으로 읽습니다."""
    pdf_path = ensure_file(DOCS / file_name)
    loader = PyPDFLoader(str(pdf_path))
    return loader.load()


def split_documents(docs: list[Document], chunk_size: int = 500, chunk_overlap: int = 50) -> list[Document]:
    """Document 목록을 지정한 크기와 겹침으로 청킹합니다."""
    if chunk_size <= 0:
        raise ValueError("chunk_size는 1 이상이어야 합니다.")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap은 0 이상이고 chunk_size보다 작아야 합니다.")
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_documents(docs)


def load_csv(file_name: str = "faq.csv") -> list[Document]:
    """CSV의 각 행을 하나의 Document로 읽습니다."""
    csv_path = ensure_file(DATA / file_name)
    return CSVLoader(file_path=str(csv_path), encoding="utf-8-sig").load()


def load_text(file_name: str = "notice.txt") -> list[Document]:
    """일반 텍스트 파일 전체를 하나의 Document로 읽습니다."""
    text_path = ensure_file(DATA / file_name)
    return TextLoader(str(text_path), encoding="utf-8").load()


def load_markdown(file_name: str = "policy.md") -> list[Document]:
    """마크다운을 1단계와 2단계 헤더 기준으로 분리합니다."""
    markdown_path = ensure_file(DATA / file_name)
    markdown_text = markdown_path.read_text(encoding="utf-8")
    splitter = MarkdownHeaderTextSplitter(headers_to_split_on=[("#", "대분류"), ("##", "소분류")])
    return splitter.split_text(markdown_text)


def load_all_sources() -> list[Document]:
    """PDF, CSV, TXT, Markdown 결과를 하나의 Document 목록으로 합칩니다."""
    return load_pdf() + load_csv() + load_text() + load_markdown()
