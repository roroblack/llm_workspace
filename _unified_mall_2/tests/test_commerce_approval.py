"""Phase 6 — 커머스 승인 루프.

결정론 단위(Fake catalog/repo, 연결 불필요) + API 통합(미리보기 무변경·멱등·충돌·경계).
DoD: 미리보기 전 DB변경 0, 승인 없는 주문 0, 멱등, 재고부족·타인주문 4xx.
"""

from __future__ import annotations

import pytest

from app.application.commerce import (
    IdempotentHit,
    OrderLine,
    PlaceOrder,
    PlacedItem,
    PlacedOrder,
    PreviewOrder,
    ProductInfo,
    request_fingerprint,
)
from app.core.errors import ConflictErr, ValidationErr
from tests.conftest import auth_header, order_headers


# --- 결정론 단위(Fake, 연결 불필요) ---------------------------------------
class _FakeCatalog:
    def __init__(self, products: dict[str, ProductInfo], stock: dict[int, int]):
        self._p = products
        self._s = stock

    def get_product(self, code):
        return self._p.get(code)

    def get_stock(self, product_id):
        return self._s.get(product_id, 0)


def _catalog():
    return _FakeCatalog(
        {"A": ProductInfo(1, "A", "사과", 1000), "B": ProductInfo(2, "B", "배", 2000)},
        {1: 5, 2: 0},
    )


def test_preview_computes_total_and_feasibility():
    pv = PreviewOrder(_catalog())([OrderLine("A", 2)])
    assert pv.total == 2000 and pv.feasible is True
    assert pv.lines[0].sufficient is True and pv.lines[0].available == 5


def test_preview_flags_insufficient_and_unknown_without_raising():
    pv = PreviewOrder(_catalog())([OrderLine("B", 1), OrderLine("NOPE", 1)])
    assert pv.feasible is False
    assert any("재고 부족" in i for i in pv.issues)
    assert any("상품 없음" in i for i in pv.issues)
    # 미상품 라인은 unit_price/available None, subtotal 0
    nope = [ln for ln in pv.lines if ln.product_code == "NOPE"][0]
    assert nope.unit_price is None and nope.subtotal == 0


def test_preview_empty_raises():
    with pytest.raises(ValidationErr):
        PreviewOrder(_catalog())([])


def test_preview_aggregates_duplicate_lines_of_same_product():
    # 재고 5(상품 A)에 A×3 + A×3 = 누적 6 > 5 → 두 번째 라인 sufficient=False, feasible=False
    pv = PreviewOrder(_catalog())([OrderLine("A", 3), OrderLine("A", 3)])
    assert pv.feasible is False
    assert pv.lines[0].sufficient is True   # 누적 3 ≤ 5
    assert pv.lines[1].sufficient is False  # 누적 6 > 5


def test_place_rejects_nonpositive_qty_even_on_idem_path():
    repo = _FakeRepo()
    uc = PlaceOrder(repo)
    uc(1, [OrderLine("A", 1)], "k1")  # 기존 주문
    # A×2 + A×-1 은 순수량 1로 지문이 같지만, 조회 전에 음수 수량을 거부해야 함
    with pytest.raises(ValidationErr):
        uc(1, [OrderLine("A", 2), OrderLine("A", -1)], "k1")


def test_fingerprint_order_and_split_invariant():
    # 순서·분할이 달라도 같은 순수량이면 동일 지문
    a = request_fingerprint([OrderLine("A", 1), OrderLine("B", 2)])
    b = request_fingerprint([OrderLine("B", 2), OrderLine("A", 1)])
    c = request_fingerprint([OrderLine("A", 1), OrderLine("B", 1), OrderLine("B", 1)])
    assert a == b == c


class _FakeRepo:
    """멱등 저장을 흉내내는 인메모리 repo. place는 호출횟수를 센다."""

    def __init__(self):
        self.store: dict[tuple[int, str], IdempotentHit] = {}
        self.place_calls = 0

    def find_by_idempotency_key(self, user_id, key):
        return self.store.get((user_id, key))

    def place(self, user_id, lines, key, request_hash):
        self.place_calls += 1
        order = PlacedOrder(
            order_no=f"O{self.place_calls}",
            status="PENDING",
            total=sum(ln.quantity for ln in lines),
            items=[PlacedItem("x", 1, ln.quantity) for ln in lines],
        )
        self.store[(user_id, key)] = IdempotentHit(order=order, request_hash=request_hash)
        return order


def test_place_requires_idempotency_key():
    with pytest.raises(ValidationErr):
        PlaceOrder(_FakeRepo())(1, [OrderLine("A", 1)], "")


def test_place_is_idempotent_same_key_same_payload():
    repo = _FakeRepo()
    uc = PlaceOrder(repo)
    o1 = uc(1, [OrderLine("A", 1)], "k1")
    o2 = uc(1, [OrderLine("A", 1)], "k1")
    assert o1.order_no == o2.order_no
    assert repo.place_calls == 1  # 두 번째는 재생 — 신규 place 없음


def test_is_unique_violation_discriminates_constraint_kind():
    from sqlalchemy.exc import IntegrityError

    from app.adapters.sql_order_repo import _is_unique_violation

    uniq = IntegrityError("s", {}, Exception("UNIQUE constraint failed: order_idempotency.user_id"))
    fk = IntegrityError("s", {}, Exception("FOREIGN KEY constraint failed"))
    assert _is_unique_violation(uniq) is True
    assert _is_unique_violation(fk) is False  # 다른 무결성 오류는 멱등 경합으로 오분류하지 않음


def test_place_same_key_different_payload_conflicts():
    repo = _FakeRepo()
    uc = PlaceOrder(repo)
    uc(1, [OrderLine("A", 1)], "k1")
    with pytest.raises(ConflictErr):
        uc(1, [OrderLine("A", 2)], "k1")  # 같은 키·다른 수량


# --- API 통합(실 앱, SQLite) ----------------------------------------------
def test_api_preview_does_not_mutate_db(client, unique_user):
    u, p = unique_user()
    headers = auth_header(client, u, p)
    stock_before = client.get("/api/products/P0001").json()["stock"]
    orders_before = len(client.get("/api/orders", headers=headers).json())

    r = client.post(
        "/api/orders/preview",
        json={"items": [{"product_code": "P0001", "quantity": 2}]},
        headers=headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["feasible"] is True
    assert body["total"] == body["lines"][0]["unit_price"] * 2

    # DB 변경 0: 재고·주문수 불변
    assert client.get("/api/products/P0001").json()["stock"] == stock_before
    assert len(client.get("/api/orders", headers=headers).json()) == orders_before


def test_api_preview_only_creates_no_order(client, unique_user):
    """승인 없는 주문 0: 미리보기만으로는 주문이 생기지 않는다."""
    u, p = unique_user()
    headers = auth_header(client, u, p)
    for _ in range(3):
        client.post(
            "/api/orders/preview",
            json={"items": [{"product_code": "P0001", "quantity": 1}]},
            headers=headers,
        )
    assert client.get("/api/orders", headers=headers).json() == []


def test_api_create_requires_idempotency_key(client, unique_user):
    u, p = unique_user()
    headers = auth_header(client, u, p)  # Idempotency-Key 없음
    r = client.post(
        "/api/orders",
        json={"items": [{"product_code": "P0001", "quantity": 1}]},
        headers=headers,
    )
    assert r.status_code == 422


def test_api_idempotent_create_decrements_stock_once(client, unique_user):
    u, p = unique_user()
    auth = auth_header(client, u, p)
    hdr = order_headers(auth, key="fixed-key-123")
    before = client.get("/api/products/P0001").json()["stock"]
    r1 = client.post(
        "/api/orders",
        json={"items": [{"product_code": "P0001", "quantity": 1}]},
        headers=hdr,
    )
    r2 = client.post(
        "/api/orders",
        json={"items": [{"product_code": "P0001", "quantity": 1}]},
        headers=hdr,
    )
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["order_no"] == r2.json()["order_no"]  # 같은 주문 재생
    after = client.get("/api/products/P0001").json()["stock"]
    assert after == before - 1  # 재고 1회만 차감
    # 주문 1건만
    assert len(client.get("/api/orders", headers=auth).json()) == 1


def test_api_same_key_different_payload_409(client, unique_user):
    u, p = unique_user()
    auth = auth_header(client, u, p)
    hdr = order_headers(auth, key="dup-key-999")
    client.post(
        "/api/orders",
        json={"items": [{"product_code": "P0001", "quantity": 1}]},
        headers=hdr,
    )
    r = client.post(
        "/api/orders",
        json={"items": [{"product_code": "P0001", "quantity": 2}]},  # 다른 수량
        headers=hdr,
    )
    assert r.status_code == 409
