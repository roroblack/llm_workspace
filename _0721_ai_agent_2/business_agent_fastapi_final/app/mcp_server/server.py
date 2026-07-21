# -*- coding: utf-8 -*-
"""표준 입출력 방식으로 독립 실행하는 Business Agent MCP 서버입니다."""

# 공식 MCP Python SDK의 간단한 서버 구현을 가져옵니다.
from mcp.server.fastmcp import FastMCP
# 실제 비즈니스 로직을 가진 순수 함수를 가져옵니다.
from app.mcp_server.tools import mcp_csv_preview, mcp_data_summary, mcp_file_list, mcp_monthly_sales

# MCP 클라이언트가 식별할 서버 이름을 지정합니다.
mcp = FastMCP("business-agent-mcp")


@mcp.tool()
def monthly_sales(month: str = "") -> str:
    """월별 매출, 전월 대비 성장률, 카테고리 순위를 조회합니다."""
    # 공유 비즈니스 함수를 호출해 결과를 반환합니다.
    return mcp_monthly_sales(month)


@mcp.tool()
def csv_preview(filename: str, limit: int = 10) -> str:
    """프로젝트 data 폴더의 CSV 파일 일부를 확인합니다."""
    # 공유 CSV 미리보기 함수를 호출합니다.
    return mcp_csv_preview(filename, limit)


@mcp.tool()
def data_summary() -> str:
    """분석 가능한 핵심 비즈니스 데이터 구성을 확인합니다."""
    # 공유 데이터 요약 함수를 호출합니다.
    return mcp_data_summary()


@mcp.tool()
def data_files() -> str:
    """data 폴더의 전체 파일 목록을 확인합니다."""
    # 공유 파일 목록 함수를 호출합니다.
    return mcp_file_list()


if __name__ == "__main__":
    # 이 파일을 직접 실행할 때 stdio 전송 방식으로 MCP 서버를 시작합니다.
    mcp.run(transport="stdio")
