"""MCP GitHub Tool 등록 함수를 제공합니다."""

# FastMCP 서버 타입을 가져옵니다.
from mcp.server.fastmcp import FastMCP

# 공용 Container를 가져옵니다.
from app.services.container import get_container


# GitHub Tool을 등록합니다.
def register_github_tools(mcp: FastMCP) -> None:
    """GitHub Issue 목록과 생성 Tool을 등록합니다."""

    # Issue 목록 Tool을 등록합니다.
    @mcp.tool()
    def github_list_issues(limit: int = 10) -> list[dict]:
        """GitHub 저장소의 최근 Issue를 반환합니다."""

        # GitHub 어댑터를 호출합니다.
        return get_container().github.list_issues(limit)

    # Issue 생성 Tool을 등록합니다.
    @mcp.tool()
    def github_create_issue(title: str, body: str) -> dict:
        """GitHub 저장소에 새 Issue를 생성합니다."""

        # GitHub 어댑터를 호출합니다.
        return get_container().github.create_issue(title, body)
