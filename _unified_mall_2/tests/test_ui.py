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


def test_new_feature_pages_served(client):
    """Phase 1~10에서 만든 기능(RAG backend·승인루프·관리자·MCP)을 UI에서 실제로
    쓸 수 있는지 — 정적 페이지가 서빙되고 해당 API 엔드포인트를 실제로 호출하는지 확인.
    """
    pages = {
        "/static/rag.html": ["backend", "faiss"],
        "/static/orders.html": ["Idempotency-Key", "미리보기"],
        "/static/admin.html": ["require_admin", "관리자"],
        "/static/mcp.html": ["get_price", "MCP"],
        "/static/video.html": ["화상 상담", "AI 상담원", "카메라 없이 텍스트로 계속"],
        "/static/mypage.html": ["얼굴 로그인", "얼굴 2차 인증", "라이브니스"],
        "/static/facebench.html": ["성능 비교", "insightface", "AdaFace", "LVFace"],
        "/static/shop.html": ["스토어", "장바구니", "주문하기"],
    }
    for path, must_contain in pages.items():
        r = client.get(path)
        assert r.status_code == 200, f"{path} 서빙 실패"
        for text in must_contain:
            assert text in r.text, f"{path}에 '{text}' 없음"


def test_new_feature_scripts_call_the_real_endpoints(client):
    """각 페이지가 실제 백엔드 엔드포인트를 호출하는지(장식용 목업이 아님).

    admin.js는 fetchApi() 호출 안에 실제 경로 문자열을 그대로 갖고 있다.
    """
    checks = {
        "/static/rag.js": ["/api/rag/search", "/api/rag/qa"],
        "/static/orders.js": ["/api/orders/preview", "/api/orders", "Idempotency-Key", "submitLogin"],
        "/static/admin.js": ["/api/admin/orders", "/api/admin/events",
                              "/api/admin/index", "/api/admin/knowledge-gaps",
                              "/api/admin/report", "submitLogin", "/api/face/status"],
        "/static/mcp.js": ["/api/mcp/tools", "/api/mcp/call"],
        # video.js는 상담을 직접 호출하고, STT/TTS는 common.js 헬퍼(createVoiceRecorder/
        # synthesizeAndPlay) 경유 — 그 헬퍼가 실제 음성 엔드포인트를 호출한다.
        "/static/video.js": ["/api/agent/chat", "createVoiceRecorder", "synthesizeAndPlay"],
        "/static/common.js": ["/api/voice/stt", "/api/voice/tts", "captureFrameBlob",
                              "/auth/login/face", "submitLogin"],
        "/static/mypage.js": ["/auth/login", "/api/face/register", "/api/face/status", "captureFrameBlob"],
        "/static/facebench.js": ["/api/face/benchmark", "/api/face/backend"],
        "/static/shop.js": ["/api/products", "/api/orders/preview", "/api/orders",
                            "Idempotency-Key", "submitLogin"],
    }
    for path, must_contain in checks.items():
        r = client.get(path)
        assert r.status_code == 200
        for text in must_contain:
            assert text in r.text, f"{path}에 '{text}' 없음"


def test_customer_and_admin_apps_are_physically_separated():
    """고객 앱(공개 포트)과 운영 앱(내부 포트)이 실제로 분리됐는지 — 관리자 API/페이지가
    고객 앱에는 물리적으로 없어야(404) 하고 운영 앱에는 있어야 한다.

    실제 프로덕션 패턴(별도 서비스/포트/서브도메인, 관리자는 VPN 뒤)의 축소판.
    """
    from fastapi.testclient import TestClient

    from app.main import admin_app, customer_app

    cust = TestClient(customer_app)
    adm = TestClient(admin_app)

    # 고객 앱: 관리자 API 라우터 자체가 없음 → 404 (401/403이 아니라)
    assert cust.get("/api/admin/orders").status_code == 404
    # 고객 앱: 운영/내부 API 라우터(rag/mcp/lab/nlp/workflow)도 물리적으로 없음 → 404.
    # (무인증 노출·모델연산 DoS 표면 축소 — 어떤 고객 페이지도 이들을 호출하지 않는다.)
    for ops_api in ("/api/rag/search", "/api/mcp/tools", "/api/nlp/sentiment",
                    "/api/lab/token-compare", "/api/workflow/ticket"):
        assert cust.post(ops_api, json={}).status_code == 404, f"고객 앱에 운영 API 노출: {ops_api}"
    # 고객 앱: 운영 정적 페이지 차단, 고객 페이지는 서빙
    assert cust.get("/static/admin.html").status_code == 404
    assert cust.get("/static/facebench.html").status_code == 404
    assert cust.get("/static/shop.html").status_code == 200
    # 고객 앱에도 있어야 하는 공개 라우터(상품·얼굴 상태 조회 등)는 살아 있음(404가 아님).
    assert cust.get("/api/products").status_code != 404
    assert cust.get("/api/face/backend").status_code != 404
    # 고객 앱 랜딩은 스토어
    assert "스토어" in cust.get("/").text

    # 운영 앱: 관리자 API 존재(미인증 401), 관리자 페이지 서빙, 운영 API도 존재(404 아님)
    assert adm.get("/api/admin/orders").status_code == 401
    assert adm.get("/static/admin.html").status_code == 200
    assert adm.post("/api/rag/search", json={}).status_code != 404


def test_customer_web_and_ops_tools_are_separated(client):
    """고객 웹(client)과 운영/개발 도구는 nav가 분리돼야 한다.

    고객 페이지(index 등)는 관리자·개발 도구를 노출하지 않고, 운영 페이지(admin 등)만
    그 도구들을 링크한다. '사용자 화면과 관리자 대시보드 별도 제공'(프로젝트설명.txt) 충족.
    """
    customer = client.get("/static/index.html").text
    # 고객 nav = 쇼핑/AI상담/화상상담/마이페이지만
    for path in ("shop.html", "video.html", "mypage.html"):
        assert path in customer
    # 고객 페이지 nav에 운영/개발 도구가 노출되면 안 됨
    for ops in ("admin.html", "mcp.html", "facebench.html", "rag.html"):
        assert ops not in customer, f"고객 웹에 운영 도구 노출: {ops}"

    # 운영 페이지(admin)는 운영 도구들을 링크
    ops_page = client.get("/static/admin.html").text
    for path in ("rag.html", "facebench.html", "mcp.html"):
        assert path in ops_page


def test_face_backend_select_endpoint(client):
    """인식 백엔드 조회는 공개, 변경은 관리자 전용(모델 로드 없이 경로만 확인 — @ml 아님)."""
    r = client.get("/api/face/backend")
    assert r.status_code == 200
    body = r.json()
    assert body["active"] in ("adaface", "lvface", "insightface")
    assert len(body["backends"]) == 3
    # 변경은 인증 필요(미인증 401)
    r = client.put("/api/face/backend", json={"backend": "insightface"})
    assert r.status_code == 401


def test_lab_token_compare_endpoint(client):
    r = client.post(
        "/api/lab/token-compare",
        json={"ko_text": "안녕하세요 반갑습니다", "en_text": "Hi there"},
    )
    assert r.status_code == 200
    assert r.json()["ko_tokens"] > 0
