"""MCP Email Tool 등록 함수를 제공합니다."""

# FastMCP 서버 타입을 가져옵니다.
from mcp.server.fastmcp import FastMCP

# 공용 Container를 가져옵니다.
from app.services.container import get_container


# Email Tool을 등록합니다.
def register_email_tools(mcp: FastMCP) -> None:
    """이메일 전송 Tool을 등록합니다."""

    # 이메일 전송 Tool을 등록합니다.
    @mcp.tool()
    def email_send(to: str, subject: str, body: str) -> dict:
        """SMTP 또는 데모 모드로 이메일을 전송합니다."""

        # Email 어댑터를 호출합니다.
        return get_container().email.send(to, subject, body)
