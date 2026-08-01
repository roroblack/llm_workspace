"""
허용 목록 기반의 안전한 Browser Tool 어댑터입니다.
"""

# HTML 태그를 간단히 제거하기 위해 re를 가져옵니다.
import re

# URL을 분석하기 위해 urlparse를 가져옵니다.
from urllib.parse import urlparse

# 웹 페이지를 요청하기 위해 httpx를 가져옵니다.
import httpx


# Browser Tool 어댑터를 정의합니다.
class BrowserAdapter:
    """사전에 허용된 호스트의 공개 웹 페이지만 읽습니다."""

    # 허용된 호스트 목록을 전달받습니다.
    def __init__(self, allowed_hosts: list[str]) -> None:
        # 모두 소문자로 변환하여 집합으로 저장합니다.
        self.allowed_hosts = {host.lower() for host in allowed_hosts}

    # URL이 안전한지 검사합니다.
    def _validate_url(self, url: str) -> None:
        """HTTP(S) 및 허용 호스트 여부를 검사합니다."""

        # URL을 구성 요소별로 분석합니다.
        parsed = urlparse(url)

        # HTTP 또는 HTTPS 외의 스킴을 차단합니다.
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("Browser Tool은 http 또는 https URL만 허용합니다.")

        # 호스트 이름을 소문자로 가져옵니다.
        hostname = (parsed.hostname or "").lower()

        # 허용 목록에 없는 호스트를 차단합니다.
        if hostname not in self.allowed_hosts:
            raise ValueError(f"허용되지 않은 호스트입니다: {hostname}")

    # 웹 페이지의 텍스트 일부를 가져옵니다.
    def fetch_text(self, url: str, max_chars: int = 5000) -> dict:
        """허용된 공개 페이지의 텍스트를 반환합니다."""

        # URL 보안 검사를 수행합니다.
        self._validate_url(url)

        # 리다이렉트를 허용하여 페이지를 요청합니다.
        response = httpx.get(
            url,
            follow_redirects=True,
            timeout=15.0,
            headers={"User-Agent": "MCP-Enterprise-Tool-Hub/1.0"},
        )

        # HTTP 실패 응답을 검사합니다.
        response.raise_for_status()

        # script와 style 영역을 제거합니다.
        cleaned = re.sub(r"<script.*?</script>|<style.*?</style>", " ", response.text, flags=re.I | re.S)

        # 나머지 HTML 태그를 공백으로 치환합니다.
        cleaned = re.sub(r"<[^>]+>", " ", cleaned)

        # 연속 공백을 하나로 정리합니다.
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # 반환 길이를 안전한 범위로 제한합니다.
        safe_limit = max(100, min(max_chars, 20000))

        # URL, 상태 코드, 텍스트 일부를 반환합니다.
        return {"url": str(response.url), "status_code": response.status_code, "text": cleaned[:safe_limit]}
