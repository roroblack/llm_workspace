# -*- coding: utf-8 -*-
"""API 키 없이 실행 가능한 실데이터 도구 단위 테스트입니다."""

# 실제 CSV 기반 서비스 함수를 가져옵니다.
from app.services.data_service import get_order_status, request_exchange, search_faq


# test_missing_order 함수는 없는 주문에 환각된 상태를 반환하지 않는지 확인합니다.
def test_missing_order() -> None:
    """없는 주문번호는 찾을 수 없다는 메시지를 반환해야 합니다."""
    # 존재하지 않는 주문번호를 조회합니다.
    result = get_order_status("O999999")
    # 안전한 실패 문구가 결과에 포함되는지 검증합니다.
    assert "찾을 수 없습니다" in result


# test_exchange_rejects_missing_order 함수는 없는 주문의 교환 접수를 막는지 확인합니다.
def test_exchange_rejects_missing_order() -> None:
    """존재하지 않는 주문에는 교환 접수번호를 생성하면 안 됩니다."""
    # 잘못된 주문번호로 교환을 요청합니다.
    result = request_exchange("O999999", "상품 불량")
    # 접수되지 않았다는 문구를 확인합니다.
    assert "접수하지 않았습니다" in result


# test_faq_returns_text 함수는 FAQ 서비스가 항상 문자열을 반환하는지 확인합니다.
def test_faq_returns_text() -> None:
    """FAQ 검색 결과는 사용자에게 표시 가능한 문자열이어야 합니다."""
    # 일반적인 배송 키워드로 검색합니다.
    result = search_faq("배송")
    # 반환 타입이 문자열인지 검증합니다.
    assert isinstance(result, str)
