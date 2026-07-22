# -*- coding: utf-8 -*-
"""FastAPI 내부에서 MCP 도구와 동일한 비즈니스 함수를 호출하는 클라이언트 추상화입니다."""

# Any는 도구마다 다른 인자 구조를 허용합니다.
from typing import Any

# 실제 데이터 서비스 함수를 가져옵니다.
from app.services.data_service import get_order_status, get_stock, request_exchange, search_faq

# LOCAL_TOOL_REGISTRY는 MCP 서버와 FastAPI가 공유하는 단일 비즈니스 함수 레지스트리입니다.
LOCAL_TOOL_REGISTRY = {
    "get_order_status": get_order_status,
    "get_stock": get_stock,
    "search_faq": search_faq,
    "request_exchange": request_exchange,
}


# call_local_mcp_tool 함수는 MCP 도구 호출과 동일한 이름 및 인자 규칙을 적용합니다.
def call_local_mcp_tool(tool_name: str, arguments: dict[str, Any]) -> str:
    """등록된 MCP 도구를 이름으로 찾아 키워드 인자로 실행합니다."""
    # 요청한 도구가 레지스트리에 있는지 확인합니다.
    if tool_name not in LOCAL_TOOL_REGISTRY:
        # 지원하지 않는 도구는 임의 실행하지 않고 오류를 반환합니다.
        return f"등록되지 않은 MCP 도구입니다: {tool_name}"
    # 도구 이름에 대응하는 파이썬 함수를 가져옵니다.
    tool_function = LOCAL_TOOL_REGISTRY[tool_name]
    # JSON 객체로 받은 인자를 키워드 인자로 펼쳐 함수를 호출합니다.
    return str(tool_function(**arguments))
