"""MCP DB Tool 등록 함수를 제공합니다."""

# FastMCP 서버 타입을 가져옵니다.
from mcp.server.fastmcp import FastMCP

# 공용 Container를 가져옵니다.
from app.services.container import get_container


# DB Tool을 등록합니다.
def register_db_tools(mcp: FastMCP) -> None:
    """업무 메모 등록, 목록, 검색 Tool을 등록합니다."""

    # 메모 등록 Tool을 등록합니다.
    @mcp.tool()
    def db_add_note(title: str, content: str) -> dict:
        """SQLite 업무 메모 테이블에 데이터를 저장합니다."""

        # 데이터베이스 어댑터를 호출합니다.
        return get_container().database.add_note(title, content)

    # 메모 목록 Tool을 등록합니다.
    @mcp.tool()
    def db_list_notes(limit: int = 20) -> list[dict]:
        """최근 업무 메모 목록을 반환합니다."""

        # 데이터베이스 어댑터를 호출합니다.
        return get_container().database.list_notes(limit)

    # 메모 검색 Tool을 등록합니다.
    @mcp.tool()
    def db_search_notes(keyword: str, limit: int = 20) -> list[dict]:
        """제목과 본문에서 업무 메모를 검색합니다."""

        # 데이터베이스 어댑터를 호출합니다.
        return get_container().database.search_notes(keyword, limit)
