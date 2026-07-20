"""admin.html 스크린샷 재캡처 — Codex CLI 기반 신규 대시보드용.

기존(버튼 클릭형 UI)과 달리 신규 대시보드는 로그인하면 준비 상태·주문·이벤트·
지식갭 4개 패널이 자동으로 로드된다(Promise.allSettled). 그래서 버튼별
data-path 클릭이 아니라 로그인/로그아웃만으로 401 → 403 → 200 사다리를 재현한다.
"""

from __future__ import annotations

import json
import urllib.request
import uuid
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:8080"
OUT = Path(__file__).resolve().parents[1] / "docs" / "screenshots"


def signup(username: str, password: str) -> None:
    req = urllib.request.Request(
        f"{BASE}/auth/signup",
        data=json.dumps({"username": username, "password": password}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    urllib.request.urlopen(req).read()


def login(page, username: str, password: str) -> None:
    page.fill("#adminUsername", username)
    page.fill("#adminPassword", password)
    page.evaluate("document.getElementById('loginStatus').textContent = ''")
    page.click("#adminLoginBtn")
    page.wait_for_function(
        "document.getElementById('loginStatus').textContent.length > 0",
        timeout=15000,
    )


def redact_token_and_status(page, status_text: str) -> None:
    # 로그인 응답에는 실 JWT가 담기지 않지만(#loginStatus는 사용자명만 표시),
    # localStorage에는 토큰이 남아 있으므로 화면에 노출되는 텍스트만 정리한다.
    page.evaluate(
        "document.getElementById('loginStatus').textContent = " + json.dumps(status_text)
    )


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(f"{BASE}/static/admin.html")

        # 9. 401 미인증 — 로그인 전 초기 로드 상태(대시보드가 자동으로 401을 맞음)
        page.wait_for_selector("#authNotice:not([hidden])", timeout=15000)
        page.screenshot(path=str(OUT / "09_admin_401_unauthenticated.png"), full_page=True)
        print("saved 09")

        # 10. 403 일반 사용자 — admin.html엔 회원가입 폼이 없으므로(관리자 페이지는 로그인 전용)
        # REST로 먼저 계정을 만든 뒤 같은 폼으로 로그인한다.
        uname = "demo_" + uuid.uuid4().hex[:8]
        signup(uname, "pass1234")
        login(page, uname, "pass1234")
        page.wait_for_selector("#authNotice:not([hidden])", timeout=15000)
        redact_token_and_status(page, f"로그인됨: {uname} (일반 사용자)")
        page.screenshot(path=str(OUT / "10_admin_403_forbidden.png"), full_page=True)
        print("saved 10")

        # 11. 200 관리자(demo_admin) — 로그인 성공 후 주문 패널이 실제 데이터로 채워짐.
        # 로그인 응답 자체는 JWT를 반환하지 않지만 localStorage에 남으므로,
        # 화면에 노출되는 상태 텍스트만 스크린샷 직전에 정리한다.
        page.click("#logoutBtn")
        login(page, "demo_admin", "demoPass123")
        page.wait_for_selector("#ordersTableBody tr", timeout=15000)
        redact_token_and_status(page, "로그인됨: demo_admin (관리자)")
        page.screenshot(path=str(OUT / "11_admin_200_orders.png"), full_page=True)
        print("saved 11")

        # 12. 인덱스/준비 상태 카드 — 같은 로그인 상태에서 상단 요약 카드가 갱신됐는지 확인
        page.wait_for_selector("#readinessValue", timeout=15000)
        page.screenshot(path=str(OUT / "12_admin_index_status.png"), full_page=True)
        print("saved 12")

        browser.close()


if __name__ == "__main__":
    main()
