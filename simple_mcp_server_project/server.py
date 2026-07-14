"""Tool, Resource, Prompt를 제공하는 간단한 MCP 서버입니다."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

from mcp.server.fastmcp import FastMCP


BASE_DIR = Path(__file__).resolve().parent
MANUAL_PATH = BASE_DIR / "data" / "manual.txt"

mcp = FastMCP(
    "simple-mcp-server",
    instructions="간단한 인사, 덧셈, 현재 시간 조회와 예제 리소스 및 프롬프트를 제공합니다.",
)


@mcp.tool()
def hello(name: str) -> str:
    """입력받은 이름으로 인사말을 만듭니다."""
    return f"안녕하세요, {name}님!"


@mcp.tool()
def add(a: float, b: float) -> float:
    """두 숫자를 더한 결과를 반환합니다."""
    return a + b


@mcp.tool()
def get_current_time() -> str:
    """서버 컴퓨터의 현재 지역 시간을 ISO 8601 형식으로 반환합니다."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


@mcp.resource("manual://guide", mime_type="text/plain")
def get_manual() -> str:
    """프로젝트에 포함된 MCP 서버 사용 설명서를 반환합니다."""
    return MANUAL_PATH.read_text(encoding="utf-8")


@mcp.resource("profile://{name}", mime_type="text/plain")
def get_profile(name: str) -> str:
    """이름을 바탕으로 학습용 예제 프로필을 생성합니다."""
    decoded_name = unquote(name)
    return (
        f"이름: {decoded_name}\n"
        "역할: MCP 학습자\n"
        "관심 분야: Model Context Protocol"
    )


@mcp.prompt()
def summarize_document(topic: str, style: str = "핵심 위주") -> str:
    """주제와 설명 방식에 맞는 문서 요약 프롬프트를 만듭니다."""
    return (
        f"다음 문서에서 '{topic}'와 관련된 내용을 찾아 요약해 주세요.\n"
        f"설명 방식: {style}\n"
        "중요한 사실은 빠뜨리지 말고, 문서에 없는 내용은 추측하지 마세요."
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
