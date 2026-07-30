"""의도 분류 테스트 (규칙기반, 결정론 — CI 포함)."""

import pytest

from app.core.errors import ValidationErr
from app.ml.intent import classify_intent


def test_order_intent():
    assert classify_intent("이 상품 주문할게요")["intent"] == "주문"


def test_recommend_intent():
    assert classify_intent("어떤 게 좋은지 추천해줘")["intent"] == "추천"


def test_inquiry_intent():
    assert classify_intent("P0001 재고 얼마나 있나요")["intent"] == "조회"


def test_complaint_intent():
    assert classify_intent("환불해주세요 정말 실망했어요")["intent"] == "불만"


def test_greeting_intent():
    assert classify_intent("안녕하세요")["intent"] == "인사"


def test_unknown_is_etc():
    r = classify_intent("음 그러니까 저기 말이죠")
    assert r["intent"] == "기타"
    assert r["confidence"] == 0.0


def test_empty_raises():
    with pytest.raises(ValidationErr):
        classify_intent("   ")


def test_tie_break_priority():
    # '주문'(우선순위0)과 '추천'(우선순위1) 키워드가 1개씩 동률 → 우선순위 앞선 '주문'
    r = classify_intent("주문할지 추천받을지 고민이에요")
    assert r["intent"] == "주문"
