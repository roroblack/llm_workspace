"""인증 테스트: 가입/로그인/토큰."""

from tests.conftest import auth_header


def test_signup_and_login(client, unique_user):
    username, password = unique_user()
    r = client.post("/auth/signup", json={"username": username, "password": password})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"

    r2 = client.post("/auth/login", data={"username": username, "password": password})
    assert r2.status_code == 200
    assert r2.json()["access_token"]


def test_duplicate_signup_rejected(client, unique_user):
    username, password = unique_user()
    client.post("/auth/signup", json={"username": username, "password": password})
    r = client.post("/auth/signup", json={"username": username, "password": password})
    assert r.status_code == 422  # ValidationErr


def test_wrong_password_401(client, unique_user):
    username, password = unique_user()
    client.post("/auth/signup", json={"username": username, "password": password})
    r = client.post("/auth/login", data={"username": username, "password": "wrong"})
    assert r.status_code == 401


def test_invalid_token_401(client):
    r = client.get("/api/orders", headers={"Authorization": "Bearer invalid.token.here"})
    assert r.status_code == 401


def test_protected_route_without_token_401(client):
    r = client.get("/api/orders")
    assert r.status_code == 401
