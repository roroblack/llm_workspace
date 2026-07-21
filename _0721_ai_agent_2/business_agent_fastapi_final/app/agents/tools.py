# -*- coding: utf-8 -*-
"""ReAct와 MCP가 공통으로 호출하는 비즈니스 도구 모음입니다."""

# 도구 결과를 JSON 문자열로 반환하기 위해 json 모듈을 가져옵니다.
import json
# LangChain 도구 데코레이터를 가져옵니다.
from langchain_core.tools import tool
# 비즈니스 데이터 서비스를 가져옵니다.
from app.services.business_service import format_facts, load_facts, load_facts_for_month
# 데이터 파일 조회 서비스를 가져옵니다.
from app.services.data_service import read_csv_preview, summarize_business_data
# RAG 검색 서비스를 가져옵니다.
from app.services.rag_service import search_knowledge
# 현재 요청의 공급자를 가져옵니다.
from app.services.provider_context import get_provider


@tool
def monthly_sales_facts(month: str = "") -> str:
    """특정 월 또는 최신 월의 총매출, 성장률, 카테고리 순위를 정확히 계산합니다."""
    # 월 문자열이 있으면 특정 월을, 없으면 최신 월을 계산합니다.
    facts = load_facts_for_month(month) if month.strip() else load_facts()
    # 사람이 읽을 수 있는 근거 수치 문자열을 반환합니다.
    return format_facts(facts)


@tool
def csv_preview(filename: str, limit: int = 10) -> str:
    """data 폴더의 CSV 파일 구조와 일부 행을 확인합니다."""
    # CSV 미리보기 결과를 가져옵니다.
    result = read_csv_preview(filename, limit)
    # 한글이 보존된 JSON 문자열로 변환해 반환합니다.
    return json.dumps(result, ensure_ascii=False, default=str)


@tool
def business_data_summary() -> str:
    """현재 프로젝트에서 분석 가능한 핵심 비즈니스 데이터 파일을 요약합니다."""
    # 데이터 서비스가 만든 요약 문자열을 그대로 반환합니다.
    return summarize_business_data()


@tool
def internal_knowledge_search(query: str) -> str:
    """정책 PDF와 핵심 CSV에서 질문과 관련된 근거를 검색합니다."""
    # 현재 요청에서 선택한 공급자로 RAG 검색을 실행합니다.
    result = search_knowledge(query=query, provider=get_provider())
    # 검색된 근거 본문을 반환합니다.
    return str(result["context"])


def build_tools() -> list[object]:
    """ReAct 에이전트가 사용할 전체 도구 목록을 반환합니다."""
    # 모든 도구 객체를 고정된 순서로 반환합니다.
    return [monthly_sales_facts, csv_preview, business_data_summary, internal_knowledge_search]
