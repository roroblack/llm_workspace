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
    }
    for path, must_contain in checks.items():
        r = client.get(path)
        assert r.status_code == 200
        for text in must_contain:
            assert text in r.text, f"{path}에 '{text}' 없음"


def test_index_nav_links_to_new_pages(client):
    r = client.get("/static/index.html")
    for path in ("rag.html", "orders.html", "video.html", "mypage.html", "facebench.html",
                 "admin.html", "mcp.html"):
        assert path in r.text


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
