"""MCP Vector Search Tool 등록 함수를 제공합니다."""

# FastMCP 서버 타입을 가져옵니다.
from mcp.server.fastmcp import FastMCP

# 공용 Container를 가져옵니다.
from app.services.container import get_container


# Vector Search Tool을 등록합니다.
def register_vector_tools(mcp: FastMCP) -> None:
    """문서 인덱싱과 검색 Tool을 등록합니다."""

    # 인덱스 재구축 Tool을 등록합니다.
    @mcp.tool()
    def vector_rebuild_index() -> dict:
        """data/vector_docs 문서를 TF-IDF 인덱스로 재구축합니다."""

        # Vector Search 어댑터를 호출합니다.
        return get_container().vector.rebuild()

    # 문서 검색 Tool을 등록합니다.
    @mcp.tool()
    def vector_search(query: str, top_k: int = 4) -> list[dict]:
        """질문과 유사한 문서를 검색합니다."""

        # Vector Search 어댑터를 호출합니다.
        return get_container().vector.search(query, top_k)
