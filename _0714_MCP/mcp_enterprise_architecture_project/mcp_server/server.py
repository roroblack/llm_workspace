"""
9개 Tool 범주와 Resource, Prompt를 제공하는 MCP 서버입니다.
"""

# FastMCP 서버 클래스를 가져옵니다.
from mcp.server.fastmcp import FastMCP

# 각 Tool 등록 함수를 가져옵니다.
from mcp_server.tools.browser_tools import register_browser_tools
from mcp_server.tools.calendar_tools import register_calendar_tools
from mcp_server.tools.db_tools import register_db_tools
from mcp_server.tools.email_tools import register_email_tools
from mcp_server.tools.file_tools import register_file_tools
from mcp_server.tools.github_tools import register_github_tools
from mcp_server.tools.python_tools import register_python_tools
from mcp_server.tools.slack_tools import register_slack_tools
from mcp_server.tools.vector_tools import register_vector_tools

# Resource 등록 함수를 가져옵니다.
from mcp_server.resources.system_resources import register_resources


# MCP 서버 객체를 생성합니다.
mcp = FastMCP("MCP Enterprise Tool Hub Server")

# File Tool을 등록합니다.
register_file_tools(mcp)

# DB Tool을 등록합니다.
register_db_tools(mcp)

# GitHub Tool을 등록합니다.
register_github_tools(mcp)

# Slack Tool을 등록합니다.
register_slack_tools(mcp)

# Browser Tool을 등록합니다.
register_browser_tools(mcp)

# Calendar Tool을 등록합니다.
register_calendar_tools(mcp)

# Email Tool을 등록합니다.
register_email_tools(mcp)

# Vector Search Tool을 등록합니다.
register_vector_tools(mcp)

# Python 계산 Tool을 등록합니다.
register_python_tools(mcp)

# Resource를 등록합니다.
register_resources(mcp)


# 재사용 가능한 업무 자동화 Prompt를 등록합니다.
@mcp.prompt()
def enterprise_workflow_prompt(request: str) -> str:
    """여러 Tool을 안전한 순서로 사용하도록 안내하는 Prompt를 반환합니다."""

    # 사용자 요청과 Tool 사용 원칙을 포함한 Prompt를 반환합니다.
    return (
        "사용자의 업무 요청을 분석하세요.\n"
        "읽기 Tool은 바로 사용할 수 있지만, 외부 시스템을 변경하는 "
        "GitHub Issue 생성, Slack 전송, Email 전송, 파일 쓰기 작업은 "
        "실행 전에 대상과 내용을 명확히 확인하세요.\n"
        "Tool 결과를 사실 근거로 사용하고 실패한 작업은 숨기지 마세요.\n\n"
        f"사용자 요청: {request}"
    )


# 이 모듈을 직접 실행할 때 stdio MCP 서버를 시작합니다.
if __name__ == "__main__":
    # 표준 입력과 표준 출력으로 MCP Client와 통신합니다.
    mcp.run(transport="stdio")
