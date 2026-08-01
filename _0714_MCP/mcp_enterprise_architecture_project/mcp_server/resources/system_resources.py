"""MCP Resource 등록 함수를 제공합니다."""

# JSON 문자열을 만들기 위해 json을 가져옵니다.
import json

# FastMCP 서버 타입을 가져옵니다.
from mcp.server.fastmcp import FastMCP

# 공용 Container를 가져옵니다.
from app.services.container import get_container


# Resource를 MCP 서버에 등록합니다.
def register_resources(mcp: FastMCP) -> None:
    """실행 설정과 Tool 카탈로그 Resource를 등록합니다."""

    # 실행 설정 Resource를 등록합니다.
    @mcp.resource("system://runtime")
    def runtime_resource() -> str:
        """민감정보를 제외한 현재 실행 설정을 반환합니다."""

        # Container를 가져옵니다.
        container = get_container()

        # 공개 가능한 설정만 구성합니다.
        data = {
            "live_mode": container.settings.live_mode,
            "openai_configured": bool(container.settings.openai_api_key),
            "github_configured": bool(container.settings.github_token),
            "slack_configured": bool(container.settings.slack_bot_token),
            "email_configured": bool(container.settings.smtp_host),
            "browser_allowed_hosts": container.settings.allowed_browser_hosts(),
        }

        # JSON 문자열로 반환합니다.
        return json.dumps(data, ensure_ascii=False, indent=2)

    # Tool 카탈로그 Resource를 등록합니다.
    @mcp.resource("system://tool-catalog")
    def tool_catalog_resource() -> str:
        """프로젝트의 Tool 범주와 용도를 반환합니다."""

        # Tool 카탈로그 데이터를 정의합니다.
        data = {
            "File Tool": "업무 파일 목록, 읽기, 쓰기",
            "DB Tool": "SQLite 업무 메모 등록, 목록, 검색",
            "GitHub Tool": "Issue 목록 및 생성",
            "Slack Tool": "채널 메시지 전송",
            "Browser Tool": "허용된 공개 웹 페이지 읽기",
            "Calendar Tool": "로컬 일정 생성 및 목록",
            "Email Tool": "SMTP 또는 데모 이메일 전송",
            "Vector Search Tool": "TF-IDF 문서 인덱싱 및 검색",
            "Python Tool": "산술 표현식 안전 계산",
        }

        # JSON 문자열로 반환합니다.
        return json.dumps(data, ensure_ascii=False, indent=2)
