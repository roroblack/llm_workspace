"""MCP File Tool 등록 함수를 제공합니다."""

# FastMCP 서버 타입을 가져옵니다.
from mcp.server.fastmcp import FastMCP

# 공용 Container를 가져옵니다.
from app.services.container import get_container


# File Tool을 MCP 서버에 등록합니다.
def register_file_tools(mcp: FastMCP) -> None:
    """파일 목록, 읽기, 쓰기 Tool을 등록합니다."""

    # 파일 목록 Tool을 등록합니다.
    @mcp.tool()
    def file_list() -> list[dict]:
        """허용된 업무 파일 목록을 반환합니다."""

        # 파일 시스템 어댑터를 호출합니다.
        return get_container().files.list_files()

    # 파일 읽기 Tool을 등록합니다.
    @mcp.tool()
    def file_read(filename: str) -> str:
        """허용된 디렉터리의 UTF-8 텍스트 파일을 읽습니다."""

        # 파일 시스템 어댑터를 호출합니다.
        return get_container().files.read_text(filename)

    # 파일 쓰기 Tool을 등록합니다.
    @mcp.tool()
    def file_write(filename: str, content: str) -> dict:
        """허용된 디렉터리에 UTF-8 텍스트 파일을 저장합니다."""

        # 파일 시스템 어댑터를 호출합니다.
        return get_container().files.write_text(filename, content)
