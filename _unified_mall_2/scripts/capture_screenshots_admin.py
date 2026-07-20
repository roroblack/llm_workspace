"""admin.html 스크린샷 재캡처 — 이전 결과 잔존(staleness) 버그 수정판.

버튼 클릭 전 결과 영역을 비워, wait_for_selector가 '새' pre.result가 실제로 다시
그려질 때까지 기다리게 한다(이전 캡처에서 403 결과가 남아있던 문제 수정).
"""

from __future__ import annotations

import uuid
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:8080"
OUT = Path(__file__).resolve().parents[1] / "docs" / "screenshots"


def clear_and_click(page, clear_sel, click_sel, wait_sel):
    page.evaluate(f"document.querySelector('{clear_sel}').innerHTML = ''")
    page.click(click_sel)
    page.wait_for_selector(wait_sel, timeout=20000)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 800})
        page.goto(f"{BASE}/static/admin.html")

        # 9. 401 미인증
        clear_and_click(page, "#adminResult", '[data-path="/api/admin/orders"]', "#adminResult pre.result")
        page.screenshot(path=str(OUT / "09_admin_401_unauthenticated.png"), full_page=True)
        print("saved 09")

        # 10. 403 일반 사용자 — admin.html엔 회원가입 폼이 없으므로(관리자 페이지는 로그인 전용)
        # REST로 먼저 계정을 만든 뒤 같은 폼으로 로그인한다.
        uname = "demo_" + uuid.uuid4().hex[:8]
        import json as _json
        import urllib.request

        req = urllib.request.Request(
            f"{BASE}/auth/signup",
            data=_json.dumps({"username": uname, "password": "pass1234"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req).read()

        page.fill("#adminUsername", uname)
        page.fill("#adminPassword", "pass1234")
        page.evaluate("document.getElementById('loginResult').innerHTML = ''")
        page.click("#adminLoginBtn")
        page.wait_for_selector("#loginResult pre.result", timeout=15000)
        clear_and_click(page, "#adminResult", '[data-path="/api/admin/orders"]', "#adminResult pre.result")
        page.evaluate(
            "document.getElementById('loginResult').innerHTML = "
            "'<span class=\"badge ok\">HTTP 200</span> (토큰은 스크린샷에서 생략)'"
        )
        page.screenshot(path=str(OUT / "10_admin_403_forbidden.png"), full_page=True)
        print("saved 10")

        # 11. 200 관리자(demo_admin) — 로그인 응답에는 실 JWT가 담기므로 화면에는 남기되
        # 스크린샷 직전에 지운다(발급된 토큰이 문서에 그대로 노출되지 않도록).
        page.fill("#adminUsername", "demo_admin")
        page.fill("#adminPassword", "demoPass123")
        page.evaluate("document.getElementById('loginResult').innerHTML = ''")
        page.click("#adminLoginBtn")
        page.wait_for_selector("#loginResult pre.result", timeout=15000)
        clear_and_click(page, "#adminResult", '[data-path="/api/admin/orders"]', "#adminResult pre.result")
        page.evaluate(
            "document.getElementById('loginResult').innerHTML = "
            "'<span class=\"badge ok\">HTTP 200</span> (토큰은 스크린샷에서 생략)'"
        )
        page.screenshot(path=str(OUT / "11_admin_200_orders.png"), full_page=True)
        print("saved 11")

        # 12. 인덱스 상태
        clear_and_click(page, "#adminResult", '[data-path="/api/admin/index"]', "#adminResult pre.result")
        page.screenshot(path=str(OUT / "12_admin_index_status.png"), full_page=True)
        print("saved 12")

        browser.close()


if __name__ == "__main__":
    main()
