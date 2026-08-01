"""MCP RAG Assistant의 FastMCP stdio 서버 진입점입니다."""

import sys

from mcp.server.fastmcp import FastMCP

from mcp_server.resources import document_catalog, runtime_config
from mcp_server.tools import (
    add_numbers,
    ask_rag,
    list_files,
    list_mysql_knowledge,
    read_file,
    rebuild_index,
    search_documents,
)


mcp = FastMCP(
    name="MCP RAG Assistant",
    instructions=(
        "docs 문서를 안전하게 읽고 검색하며, 검색 근거를 사용해 질문에 답하는 "
        "교육용 MCP 서버입니다. RAG 검색 전에는 rebuild_rag_index를 실행하세요."
    ),
)


@mcp.tool(name="add")
def add(a: float, b: float) -> float:
    """두 숫자를 더합니다."""

    return add_numbers(a, b)


@mcp.tool(name="list_document_files")
def list_document_files() -> list[str]:
    """서버의 docs 폴더에서 읽을 수 있는 파일 목록을 반환합니다."""

    return list_files()


@mcp.tool(name="read_document_file")
def read_document_file(filename: str) -> str:
    """docs 폴더 안의 UTF-8 문서 내용을 읽습니다."""

    return read_file(filename)


@mcp.tool(name="vector_search")
def vector_search(query: str, top_k: int = 4) -> list[dict]:
    """질문과 유사한 문서 청크를 최대 top_k개 검색합니다."""

    return search_documents(query, top_k)


@mcp.tool(name="rebuild_rag_index")
def rebuild_rag_index() -> dict:
    """docs 폴더 전체를 사용해 벡터 인덱스를 다시 구축합니다."""

    return rebuild_index()


@mcp.tool(name="rag_question_answer")
def rag_question_answer(question: str, top_k: int = 4) -> dict:
    """검색된 문서를 근거로 답변, 출처, 검색 결과를 반환합니다."""

    return ask_rag(question, top_k)


@mcp.tool(name="mysql_knowledge_list")
def mysql_knowledge_list() -> list[dict]:
    """MySQL knowledge_items 테이블의 데이터를 최신 순으로 조회합니다."""

    return list_mysql_knowledge()


@mcp.resource(
    "config://runtime",
    name="runtime_config",
    description="비밀값을 제외한 현재 애플리케이션 실행 설정",
    mime_type="application/json",
)
def config_runtime_resource() -> str:
    """현재 실행 설정을 JSON Resource로 반환합니다."""

    return runtime_config()


@mcp.resource(
    "docs://catalog",
    name="document_catalog",
    description="RAG와 파일 Tool에서 사용할 수 있는 문서 목록",
    mime_type="application/json",
)
def docs_catalog_resource() -> str:
    """문서 카탈로그를 JSON Resource로 반환합니다."""

    return document_catalog()


@mcp.prompt(name="grounded_rag_prompt")
def grounded_rag_prompt(question: str) -> str:
    """문서 검색을 먼저 수행하고 검색 근거만 사용하도록 지시합니다."""

    if not question.strip():
        raise ValueError("question은 비어 있을 수 없습니다.")

    return (
        "먼저 vector_search 또는 rag_question_answer tool 을 사용하세요\n"
        "검색 결과에 포함된 문서만 근거로 답하세요\n"
        "확인할 수 없는 내용은 추측하지 마세요\n"
        f"사용자 질문 : {question}"
    )


def main() -> None:
    """MCP Client와 통신하는 stdio 서버를 실행합니다."""

    # Windows의 기본 CP949가 UTF-8 기반 MCP JSON-RPC를 손상하지 않도록 고정합니다.
    for stream in (sys.stdin, sys.stdout):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
