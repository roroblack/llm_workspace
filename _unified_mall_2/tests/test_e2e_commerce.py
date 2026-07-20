"""E2E: 가입 → 로그인 → 주문 → 결제 (DoD 핵심 시나리오)."""

from tests.conftest import auth_header, order_headers


def test_signup_login_order_pay_flow(client, unique_user):
    u, p = unique_user()
    headers = auth_header(client, u, p)

    # 주문 생성
    order = client.post(
        "/api/orders",
        json={"items": [{"product_code": "P0001", "quantity": 2}]},
        headers=order_headers(headers),
    ).json()
    order_no = order["order_no"]
    assert order["status"] == "PENDING"
    total = order["total_amount"]

    # 결제 (금액은 서버가 주문 합계에서 계산)
    pay = client.post(
        "/api/payments",
        json={"order_no": order_no, "method": "card"},
        headers=headers,
    )
    assert pay.status_code == 200
    assert pay.json()["amount"] == total
    assert pay.json()["status"] == "PAID"

    # 주문이 PAID로 전환됐는지
    fetched = client.get(f"/api/orders/{order_no}", headers=headers).json()
    assert fetched["status"] == "PAID"

    # 결제 조회
    got = client.get(f"/api/payments/{order_no}", headers=headers)
    assert got.status_code == 200
    assert got.json()["amount"] == total


def test_double_payment_rejected(client, unique_user):
    u, p = unique_user()
    headers = auth_header(client, u, p)
    order_no = client.post(
        "/api/orders",
        json={"items": [{"product_code": "P0001", "quantity": 1}]},
        headers=order_headers(headers),
    ).json()["order_no"]
    client.post("/api/payments", json={"order_no": order_no, "method": "card"}, headers=headers)
    # 중복 결제 → 422
    r = client.post(
        "/api/payments", json={"order_no": order_no, "method": "card"}, headers=headers
    )
    assert r.status_code == 422


def test_pay_others_order_forbidden(client, unique_user):
    ua, pa = unique_user()
    ha = auth_header(client, ua, pa)
    order_no = client.post(
        "/api/orders",
        json={"items": [{"product_code": "P0001", "quantity": 1}]},
        headers=order_headers(ha),
    ).json()["order_no"]

    ub, pb = unique_user()
    hb = auth_header(client, ub, pb)
    r = client.post(
        "/api/payments", json={"order_no": order_no, "method": "card"}, headers=hb
    )
    assert r.status_code == 403
