"""MCP Calendar Tool 등록 함수를 제공합니다."""

# FastMCP 서버 타입을 가져옵니다.
from mcp.server.fastmcp import FastMCP

# 공용 Container를 가져옵니다.
from app.services.container import get_container


# Calendar Tool을 등록합니다.
def register_calendar_tools(mcp: FastMCP) -> None:
    """일정 생성과 목록 Tool을 등록합니다."""

    # 일정 생성 Tool을 등록합니다.
    @mcp.tool()
    def calendar_create_event(title: str, start: str, end: str, description: str = "") -> dict:
        """ISO 8601 형식으로 새 일정을 생성합니다."""

        # Calendar 어댑터를 호출합니다.
        return get_container().calendar.create_event(title, start, end, description)

    # 일정 목록 Tool을 등록합니다.
    @mcp.tool()
    def calendar_list_events() -> list[dict]:
        """저장된 전체 일정을 반환합니다."""

        # Calendar 어댑터를 호출합니다.
        return get_container().calendar.list_events()
