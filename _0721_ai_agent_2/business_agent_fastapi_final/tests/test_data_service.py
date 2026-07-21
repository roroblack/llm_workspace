# -*- coding: utf-8 -*-
"""API 키 없이 실행 가능한 핵심 데이터 서비스 테스트입니다."""

# 실제 확정 facts 계산 함수를 가져옵니다.
from app.services.business_service import load_facts, load_facts_for_month
# 데이터 파일 목록과 CSV 미리보기 함수를 가져옵니다.
from app.services.data_service import list_data_files, read_csv_preview


def test_latest_sales_facts() -> None:
    """최신 월 facts가 유효한 구조인지 검사합니다."""
    # 최신 월 facts를 계산합니다.
    facts = load_facts()
    # 최신 월이 원본 데이터의 마지막 월인지 확인합니다.
    assert facts["month"] == "2026-05"
    # 총매출이 양수인지 확인합니다.
    assert facts["total"] > 0
    # 카테고리 집계가 비어 있지 않은지 확인합니다.
    assert facts["by_category"]


def test_specific_month_facts() -> None:
    """특정 월과 전월 비교가 정상 동작하는지 검사합니다."""
    # 2026-04 월 facts를 계산합니다.
    facts = load_facts_for_month("2026-04")
    # 대상 월과 전월 값이 정확한지 확인합니다.
    assert facts["month"] == "2026-04"
    assert facts["prev_month"] == "2026-03"


def test_data_files_and_preview() -> None:
    """원본 데이터 파일 유지와 CSV 미리보기를 검사합니다."""
    # 전체 데이터 파일을 조회합니다.
    files = list_data_files()
    # monthly_sales.csv가 포함되어 있는지 확인합니다.
    assert any(item["path"] == "monthly_sales.csv" for item in files)
    # 월별 매출 CSV의 앞 2개 행을 읽습니다.
    preview = read_csv_preview("monthly_sales.csv", 2)
    # 요청한 행 수가 반환되었는지 확인합니다.
    assert len(preview["rows"]) == 2
