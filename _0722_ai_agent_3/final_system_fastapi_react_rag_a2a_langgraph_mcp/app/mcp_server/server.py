# -*- coding: utf-8 -*-
"""독립 실행 가능한 Model Context Protocol 도구 서버입니다."""

# FastMCP는 공식 MCP Python SDK가 제공하는 간결한 서버 API입니다.
from mcp.server.fastmcp import FastMCP

# CSV 기반 비즈니스 서비스 함수를 가져옵니다.
from app.services.data_service import get_order_status, get_stock, request_exchange, search_faq

# FastMCP 서버 객체를 이름과 함께 생성합니다.
mcp = FastMCP("승승장구몰 CS Tools")


# mcp_order_status는 주문 조회 기능을 MCP 도구로 공개합니다.
@mcp.tool()
def mcp_order_status(order_id: str) -> str:
    """주문번호로 실제 주문 상태를 조회합니다."""
    # 공통 서비스 함수를 호출해 동일한 비즈니스 규칙을 재사용합니다.
    return get_order_status(order_id)


# mcp_stock은 재고 조회 기능을 MCP 도구로 공개합니다.
@mcp.tool()
def mcp_stock(product_name: str) -> str:
    """상품명으로 실제 재고 수량을 조회합니다."""
    # 공통 재고 서비스 결과를 반환합니다.
    return get_stock(product_name)


# mcp_faq는 FAQ 검색 기능을 MCP 도구로 공개합니다.
@mcp.tool()
def mcp_faq(keyword: str) -> str:
    """키워드와 관련된 FAQ를 검색합니다."""
    # 공통 FAQ 검색 서비스 결과를 반환합니다.
    return search_faq(keyword)


# mcp_request_exchange는 교환 접수 기능을 MCP 쓰기 도구로 공개합니다.
@mcp.tool()
def mcp_request_exchange(order_id: str, reason: str) -> str:
    """실제 주문을 검증하고 교환을 접수합니다."""
    # 공통 교환 서비스 함수로 주문 검증과 접수번호 생성을 수행합니다.
    return request_exchange(order_id, reason)


# 직접 실행할 때 stdio 전송 방식의 MCP 서버를 시작합니다.
if __name__ == "__main__":
    # stdio는 Claude Desktop, Cursor 같은 MCP 클라이언트가 표준 입출력으로 연결할 때 사용합니다.
    mcp.run(transport="stdio")
