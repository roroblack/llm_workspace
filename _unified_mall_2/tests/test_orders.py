"""주문 테스트: 생성·재고·본인조회·403·seed."""

from tests.conftest import auth_header, order_headers


def test_products_seeded(client):
    r = client.get("/api/products")
    assert r.status_code == 200
    products = r.json()
    assert len(products) == 5
    codes = {p["product_code"] for p in products}
    assert "P0001" in codes


def test_seed_idempotent():
    """seed를 반복 실행해도 Product 수가 늘지 않는다 (멱등)."""
    from app.db.database import SessionLocal
    from app.db.models import Product
    from app.db.seed import seed_products

    db = SessionLocal()
    try:
        before = db.query(Product).count()
        seed_products(db)
        seed_products(db)
        after = db.query(Product).count()
        assert before == after == 5
    finally:
        db.close()


def test_create_order_snapshot_and_total(client, unique_user):
    u, p = unique_user()
    headers = auth_header(client, u, p)
    r = client.post(
        "/api/orders",
        json={"items": [{"product_code": "P0001", "quantity": 2}]},
        headers=order_headers(headers),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "PENDING"
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["quantity"] == 2
    assert body["total_amount"] == item["unit_price"] * 2


def test_stock_decremented(client, unique_user):
    u, p = unique_user()
    headers = auth_header(client, u, p)
    before = client.get("/api/products/P0001").json()["stock"]
    client.post(
        "/api/orders",
        json={"items": [{"product_code": "P0001", "quantity": 1}]},
        headers=order_headers(headers),
    )
    after = client.get("/api/products/P0001").json()["stock"]
    assert after == before - 1


def test_insufficient_stock_422(client, unique_user):
    u, p = unique_user()
    headers = auth_header(client, u, p)
    r = client.post(
        "/api/orders",
        json={"items": [{"product_code": "P0002", "quantity": 99999}]},
        headers=order_headers(headers),
    )
    assert r.status_code == 422


def test_unknown_product_404(client, unique_user):
    u, p = unique_user()
    headers = auth_header(client, u, p)
    r = client.post(
        "/api/orders",
        json={"items": [{"product_code": "NOPE", "quantity": 1}]},
        headers=order_headers(headers),
    )
    assert r.status_code == 404


def test_other_users_order_forbidden_403(client, unique_user):
    # user A 주문 생성
    ua, pa = unique_user()
    ha = auth_header(client, ua, pa)
    order_no = client.post(
        "/api/orders",
        json={"items": [{"product_code": "P0001", "quantity": 1}]},
        headers=order_headers(ha),
    ).json()["order_no"]

    # user B가 A의 주문 조회 시도 → 403
    ub, pb = unique_user()
    hb = auth_header(client, ub, pb)
    r = client.get(f"/api/orders/{order_no}", headers=hb)
    assert r.status_code == 403
