"""MCP Server에서 공개할 Tool의 애플리케이션 로직을 정의합니다."""

from app.services.container import get_container
from app.tools.file_tools import list_doc_files, read_doc_file


def _validate_top_k(top_k: int) -> None:
    """검색 결과 개수를 REST API와 같은 범위로 제한합니다."""

    if not 1 <= top_k <= 20:
        raise ValueError("top_k는 1 이상 20 이하여야 합니다.")


def add_numbers(a: float, b: float) -> float:
    """두 숫자의 합을 반환합니다."""

    return a + b


def list_files() -> list[str]:
    """MCP Client가 읽을 수 있는 문서 파일 목록을 반환합니다."""

    docs_dir = get_container().settings.docs_dir
    return list_doc_files(docs_dir)


def read_file(filename: str) -> str:
    """docs 폴더 안에 있는 UTF-8 문서 하나를 반환합니다."""

    if not filename.strip():
        raise ValueError("filename은 비어 있을 수 없습니다.")

    docs_dir = get_container().settings.docs_dir
    return read_doc_file(docs_dir, filename)


def search_documents(query: str, top_k: int = 4) -> list[dict]:
    """FAISS 또는 Qdrant에서 질문과 유사한 문서를 검색합니다."""

    if not query.strip():
        raise ValueError("query는 비어 있을 수 없습니다.")
    _validate_top_k(top_k)
    return get_container().rag_service.search(query, top_k)


def rebuild_index() -> dict:
    """docs 폴더 전체를 읽어 벡터 인덱스를 다시 구축합니다."""

    return get_container().rag_service.rebuild_index()


def ask_rag(question: str, top_k: int = 4) -> dict:
    """검색 문서를 근거로 질문에 답하고 출처를 반환합니다."""

    if not question.strip():
        raise ValueError("question은 비어 있을 수 없습니다.")
    _validate_top_k(top_k)
    return get_container().rag_service.ask(question, top_k)


def list_mysql_knowledge() -> list[dict]:
    """MySQL knowledge_items 테이블의 데이터를 최신 순으로 반환합니다."""

    return get_container().mysql_service.list_items()

