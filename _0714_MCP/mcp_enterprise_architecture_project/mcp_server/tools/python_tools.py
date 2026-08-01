"""MCP Python 실행 Tool 등록 함수를 제공합니다."""

# FastMCP 서버 타입을 가져옵니다.
from mcp.server.fastmcp import FastMCP

# 공용 Container를 가져옵니다.
from app.services.container import get_container


# 안전한 Python Tool을 등록합니다.
def register_python_tools(mcp: FastMCP) -> None:
    """산술 표현식 전용 Python 계산 Tool을 등록합니다."""

    # 계산 Tool을 등록합니다.
    @mcp.tool()
    def python_calculate(expression: str) -> dict:
        """숫자와 기본 산술 연산만 안전하게 계산합니다."""

        # Python Sandbox 어댑터를 호출합니다.
        return get_container().python.evaluate(expression)
