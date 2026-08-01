"""
FastAPI에서 MCP 서버를 하위 프로세스로 연결하는 stdio MCP Client입니다.
"""

# 비동기 컨텍스트 관리를 위해 AsyncExitStack을 가져옵니다.
from contextlib import AsyncExitStack

# 현재 Python 실행 파일 경로를 사용하기 위해 sys를 가져옵니다.
import sys

# MCP ClientSession을 가져옵니다.
from mcp import ClientSession

# stdio 서버 연결 파라미터와 연결 함수를 가져옵니다.
from mcp.client.stdio import StdioServerParameters, stdio_client

# 프로젝트 설정을 가져옵니다.
from app.core.settings import get_settings


# MCP Client 서비스 클래스를 정의합니다.
class MCPClientService:
    """요청마다 MCP 서버를 실행하고 Tool을 호출하는 간단한 Client입니다."""

    # 서버에 연결하고 Tool 목록을 반환합니다.
    async def list_tools(self) -> list[dict]:
        """MCP 서버가 제공하는 Tool 스키마 목록을 반환합니다."""

        # 서버 모듈 이름을 설정에서 가져옵니다.
        module_name = get_settings().mcp_server_module

        # 현재 가상환경의 Python으로 MCP 서버 모듈을 실행하도록 설정합니다.
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", module_name],
        )

        # stdio 연결을 엽니다.
        async with stdio_client(parameters) as (read_stream, write_stream):
            # MCP 세션을 생성합니다.
            async with ClientSession(read_stream, write_stream) as session:
                # 초기화 핸드셰이크를 수행합니다.
                await session.initialize()

                # Tool 목록을 요청합니다.
                response = await session.list_tools()

                # JSON 직렬화 가능한 딕셔너리 목록으로 변환합니다.
                return [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema,
                    }
                    for tool in response.tools
                ]

    # 이름과 인수로 Tool을 호출합니다.
    async def call_tool(self, name: str, arguments: dict) -> dict:
        """MCP 서버의 지정 Tool을 호출하고 결과를 반환합니다."""

        # 서버 모듈 이름을 가져옵니다.
        module_name = get_settings().mcp_server_module

        # MCP 서버 실행 파라미터를 구성합니다.
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", module_name],
        )

        # stdio 연결을 엽니다.
        async with stdio_client(parameters) as (read_stream, write_stream):
            # MCP 세션을 엽니다.
            async with ClientSession(read_stream, write_stream) as session:
                # 초기화 핸드셰이크를 수행합니다.
                await session.initialize()

                # Tool을 호출합니다.
                result = await session.call_tool(name, arguments=arguments)

                # 구조화된 결과가 있으면 우선 반환합니다.
                if result.structuredContent is not None:
                    return {
                        "is_error": bool(result.isError),
                        "structured_content": result.structuredContent,
                    }

                # 텍스트 또는 기타 콘텐츠를 문자열로 정리합니다.
                contents = [
                    item.text if hasattr(item, "text") else str(item)
                    for item in result.content
                ]

                # 오류 여부와 콘텐츠를 반환합니다.
                return {"is_error": bool(result.isError), "content": contents}
