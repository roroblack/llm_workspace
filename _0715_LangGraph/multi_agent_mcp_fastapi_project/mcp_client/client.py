# -*- coding: utf-8 -*-
"""STDIO 방식으로 로컬 MCP Server에 연결하는 테스트 클라이언트입니다."""
import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main() -> None:
    params = StdioServerParameters(command=sys.executable, args=["-m", "mcp_server.server"])
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("[MCP 도구 목록]")
            for tool in tools.tools:
                print("-", tool.name, ":", tool.description)
            result = await session.call_tool("search_faq", {"query": "환불 기간", "limit": 2})
            print("\n[MCP 도구 호출 결과]")
            for content in result.content:
                print(getattr(content, "text", content))

if __name__ == "__main__":
    asyncio.run(main())
