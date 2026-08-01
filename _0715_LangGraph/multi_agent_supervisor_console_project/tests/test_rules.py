# -*- coding: utf-8 -*-
"""외부 API를 호출하지 않는 규칙 및 CSV 도구 테스트입니다."""

from __future__ import annotations

import sys
from pathlib import Path

# 프로젝트의 code 폴더를 테스트 모듈 검색 경로에 추가합니다.
CODE_DIR = Path(__file__).resolve().parents[1] / "code"

# 아직 검색 경로에 없다면 맨 앞에 추가합니다.
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from data_repository import search_faq, search_products
from router import route_rule
from torch_evaluation import evaluate_rule_router


def test_policy_keyword_routes_to_policy() -> None:
    """환불 키워드가 정책 에이전트로 분류되는지 확인합니다."""
    assert route_rule("환불은 며칠 안에 해야 하나요?").target == "policy"


def test_sales_keyword_routes_to_sales() -> None:
    """추천 키워드가 상품 추천 에이전트로 분류되는지 확인합니다."""
    assert route_rule("전자기기 추천해 주세요").target == "sales"


def test_ambiguous_question_returns_unknown() -> None:
    """명시적인 키워드가 없는 질문은 하이브리드용 unknown인지 확인합니다."""
    assert route_rule("주문한 거 무를 수 있어?").target == "unknown"


def test_product_search_returns_seed_product() -> None:
    """상품 CSV 검색 결과에 전자기기 상품이 포함되는지 확인합니다."""
    assert "스마트워치" in search_products("전자기기")


def test_faq_search_returns_refund_policy() -> None:
    """FAQ 검색 결과에 환불 기간 근거가 포함되는지 확인합니다."""
    result = search_faq("환불")
    assert "7일" in result


def test_torch_rule_evaluation_has_expected_size() -> None:
    """PyTorch 평가가 전체 테스트셋을 처리하는지 확인합니다."""
    result = evaluate_rule_router()
    assert result.total == 10
    assert 0.0 <= result.accuracy <= 1.0
