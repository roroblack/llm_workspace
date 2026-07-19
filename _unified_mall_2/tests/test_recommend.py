"""상품 추천 테스트 (실 임베딩, @ml — CI 제외)."""

import pytest

from app.core.errors import ValidationErr
from app.db.database import SessionLocal
from app.ml.recommend import recommend_products

pytestmark = pytest.mark.ml


def test_recommend_returns_topk_sorted():
    db = SessionLocal()
    try:
        r = recommend_products(db, "무선 이어폰 음악 듣기 좋은 제품", top_k=3)
        assert r["count"] == 3
        scores = [x["score"] for x in r["results"]]
        assert scores == sorted(scores, reverse=True)  # 내림차순
        assert all("code" in x and "name" in x for x in r["results"])
    finally:
        db.close()


def test_recommend_empty_query_raises():
    db = SessionLocal()
    try:
        with pytest.raises(ValidationErr):
            recommend_products(db, "  ")
    finally:
        db.close()


def test_recommend_topk_zero_raises():
    db = SessionLocal()
    try:
        with pytest.raises(ValidationErr):
            recommend_products(db, "이어폰", top_k=0)
    finally:
        db.close()
