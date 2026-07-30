"""커머스 도구 단위 테스트 (실 DB, 결정론적)."""

from app.db.database import SessionLocal
from app.tools import commerce_tools as T


def _db():
    return SessionLocal()


def test_get_price_ok():
    db = _db()
    try:
        r = T.get_price(db, "P0001")
        assert r["ok"] is True
        assert r["price"] > 0
    finally:
        db.close()


def test_get_price_not_found_returns_structured_fail():
    db = _db()
    try:
        r = T.get_price(db, "NOPE")
        assert r["ok"] is False
        assert r["error_code"] == "product_not_found"
    finally:
        db.close()


def test_get_stock_need_reorder_flag():
    db = _db()
    try:
        r = T.get_stock(db, "P0002")  # 재고 3, 재주문기준 30 → need_reorder True
        assert r["ok"] is True
        assert r["need_reorder"] is True
    finally:
        db.close()


def test_search_product():
    db = _db()
    try:
        r = T.search_product(db, "바로봄")
        assert r["ok"] is True
        assert r["count"] >= 1
    finally:
        db.close()


def test_get_exchange_rate_ok_and_fail():
    db = _db()
    try:
        assert T.get_exchange_rate(db, "usd")["ok"] is True
        bad = T.get_exchange_rate(db, "XYZ")
        assert bad["ok"] is False
        assert bad["error_code"] == "currency_not_supported"
    finally:
        db.close()


def test_order_status_not_found():
    db = _db()
    try:
        r = T.get_order_status(db, "O_NOPE")
        assert r["ok"] is False
        assert r["error_code"] == "order_not_found"
    finally:
        db.close()
