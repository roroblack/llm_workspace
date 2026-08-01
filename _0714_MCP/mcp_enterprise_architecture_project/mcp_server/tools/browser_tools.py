"""MCP Browser Tool 등록 함수를 제공합니다."""

# FastMCP 서버 타입을 가져옵니다.
from mcp.server.fastmcp import FastMCP

# 공용 Container를 가져옵니다.
from app.services.container import get_container


# Browser Tool을 등록합니다.
def register_browser_tools(mcp: FastMCP) -> None:
    """허용 목록 기반 웹 페이지 읽기 Tool을 등록합니다."""

    # 웹 페이지 읽기 Tool을 등록합니다.
    @mcp.tool()
    def browser_fetch_text(url: str, max_chars: int = 5000) -> dict:
        """허용된 공개 URL의 텍스트를 반환합니다."""

        # Browser 어댑터를 호출합니다.
        return get_container().browser.fetch_text(url, max_chars)
