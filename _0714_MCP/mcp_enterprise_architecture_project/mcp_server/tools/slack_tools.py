"""MCP Slack Tool 등록 함수를 제공합니다."""

# FastMCP 서버 타입을 가져옵니다.
from mcp.server.fastmcp import FastMCP

# 공용 Container를 가져옵니다.
from app.services.container import get_container


# Slack Tool을 등록합니다.
def register_slack_tools(mcp: FastMCP) -> None:
    """Slack 메시지 전송 Tool을 등록합니다."""

    # Slack 메시지 Tool을 등록합니다.
    @mcp.tool()
    def slack_post_message(text: str, channel: str = "") -> dict:
        """Slack 채널에 메시지를 전송합니다."""

        # Slack 어댑터를 호출합니다.
        return get_container().slack.post_message(text, channel)
