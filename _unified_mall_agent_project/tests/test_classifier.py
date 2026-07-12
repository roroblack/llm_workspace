"""분류·정확도·혼동쌍 테스트 (결정론, mock chat_complete)."""

import pytest

from app.core.errors import ValidationErr
from app.prompts.classifier import (
    UNCLASSIFIED,
    classify_one,
    confusion_pairs,
    load_cs_dataset,
    measure_accuracy,
    normalize_category,
    suggest_fewshot_candidates,
)


def test_normalize_exactly_one():
    assert normalize_category("결제") == "결제"
    assert normalize_category("이건 결제 문의입니다") == "결제"


def test_normalize_zero_or_multiple_is_unclassified():
    assert normalize_category("잘 모르겠어요") == UNCLASSIFIED
    assert normalize_category("결제 아니면 환불") == UNCLASSIFIED  # 2개


def test_classify_one_with_mock():
    assert classify_one("카드 이중청구", chat_complete=lambda p: "결제") == "결제"


def test_classify_one_empty_raises():
    with pytest.raises(ValidationErr):
        classify_one("   ", chat_complete=lambda p: "결제")


def test_measure_accuracy():
    preds = ["결제", "환불", "배송"]
    labels = ["결제", "교환", "배송"]
    r = measure_accuracy(preds, labels)
    assert r["total"] == 3
    assert r["correct"] == 2
    assert r["accuracy"] == round(2 / 3, 4)
    assert r["wrong"] == [(1, "교환", "환불")]


def test_confusion_pairs_and_candidates():
    preds = ["환불", "환불", "배송"]
    labels = ["교환", "교환", "배송"]
    pairs = confusion_pairs(preds, labels)
    assert pairs == {("교환", "환불"): 2}
    cand = suggest_fewshot_candidates(preds, labels, top_n=1)
    assert cand[0]["true_label"] == "교환"
    assert cand[0]["predicted"] == "환불"
    assert cand[0]["count"] == 2


def test_confusion_pairs_length_mismatch_raises():
    with pytest.raises(ValidationErr):
        confusion_pairs(["결제"], ["결제", "환불"])


def test_load_cs_dataset():
    texts, labels = load_cs_dataset()
    assert len(texts) == 60
    assert len(labels) == 60
    assert "결제" in set(labels)
