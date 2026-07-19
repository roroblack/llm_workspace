"""정적 UI 로드 테스트 (브라우저 E2E 아님, 로드/연동 payload 범위)."""


def test_index_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "에이전트" in r.text


def test_static_js_served(client):
    r = client.get("/static/app.js")
    assert r.status_code == 200
    # UI가 실제 응답 스키마(action/observation)와 엔드포인트를 사용하는지
    assert "/api/agent/chat" in r.text
    assert "stopped_by" in r.text
    assert "observation" in r.text


def test_lab_token_compare_endpoint(client):
    r = client.post(
        "/api/lab/token-compare",
        json={"ko_text": "안녕하세요 반갑습니다", "en_text": "Hi there"},
    )
    assert r.status_code == 200
    assert r.json()["ko_tokens"] > 0
