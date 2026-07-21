# -*- coding: utf-8 -*-
"""독립 MCP 서버와 FastAPI 내부 호출이 공유하는 순수 비즈니스 함수입니다."""

# JSON 문자열로 결과를 직렬화하기 위해 json 모듈을 가져옵니다.
import json
# 월별 매출 계산 서비스를 가져옵니다.
from app.services.business_service import format_facts, load_facts, load_facts_for_month
# CSV 및 데이터 파일 조회 서비스를 가져옵니다.
from app.services.data_service import list_data_files, read_csv_preview, summarize_business_data


def mcp_monthly_sales(month: str = "") -> str:
    """특정 월 또는 최신 월의 매출 facts를 반환합니다."""
    # 월이 있으면 특정 월, 없으면 최신 월 데이터를 계산합니다.
    facts = load_facts_for_month(month) if month.strip() else load_facts()
    # 확정 수치 문자열을 반환합니다.
    return format_facts(facts)


def mcp_csv_preview(filename: str, limit: int = 10) -> str:
    """지정한 CSV의 컬럼과 일부 행을 JSON 문자열로 반환합니다."""
    # 데이터 서비스 결과를 한글 JSON 문자열로 변환해 반환합니다.
    return json.dumps(read_csv_preview(filename, limit), ensure_ascii=False, default=str)


def mcp_data_summary() -> str:
    """핵심 비즈니스 데이터 파일 구성을 요약합니다."""
    # 데이터 서비스의 요약 문자열을 반환합니다.
    return summarize_business_data()


def mcp_file_list() -> str:
    """data 폴더의 전체 파일 목록을 JSON 문자열로 반환합니다."""
    # 전체 파일 목록을 한글 JSON 문자열로 변환해 반환합니다.
    return json.dumps(list_data_files(), ensure_ascii=False)
