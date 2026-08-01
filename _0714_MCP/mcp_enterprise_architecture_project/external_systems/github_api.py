"""
GitHub REST API 또는 데모 모드를 제공하는 어댑터입니다.
"""

# HTTP 요청을 보내기 위해 httpx를 가져옵니다.
import httpx


# GitHub 어댑터를 정의합니다.
class GitHubAdapter:
    """설정에 따라 실제 GitHub Issue를 조회·생성하거나 데모 응답을 반환합니다."""

    # GitHub 연결 설정을 전달받습니다.
    def __init__(self, live_mode: bool, token: str, owner: str, repo: str) -> None:
        # 실제 호출 여부를 저장합니다.
        self.live_mode = live_mode

        # GitHub 토큰을 저장합니다.
        self.token = token

        # 저장소 소유자를 저장합니다.
        self.owner = owner

        # 저장소 이름을 저장합니다.
        self.repo = repo

    # 공통 요청 헤더를 생성합니다.
    def _headers(self) -> dict[str, str]:
        """GitHub REST API 권장 헤더를 반환합니다."""

        # Bearer 인증과 GitHub API 버전 헤더를 반환합니다.
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    # 최근 Issue를 조회합니다.
    def list_issues(self, limit: int = 10) -> list[dict]:
        """최근 GitHub Issue 목록을 반환합니다."""

        # 데모 모드이면 외부 API를 호출하지 않고 예제 데이터를 반환합니다.
        if not self.live_mode:
            return [
                {
                    "number": 1,
                    "title": "[DEMO] MCP Tool 연동 점검",
                    "state": "open",
                    "html_url": "https://github.com/demo/repository/issues/1",
                }
            ]

        # 실제 호출에 필요한 설정이 모두 있는지 확인합니다.
        if not all([self.token, self.owner, self.repo]):
            raise RuntimeError("GitHub live 모드 설정이 부족합니다.")

        # GitHub Issues API 주소를 구성합니다.
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/issues"

        # 최근 Issue를 요청합니다.
        response = httpx.get(
            url,
            headers=self._headers(),
            params={"per_page": max(1, min(limit, 100)), "state": "all"},
            timeout=15.0,
        )

        # 실패 응답이면 HTTP 오류를 발생시킵니다.
        response.raise_for_status()

        # 필요한 필드만 정리하여 반환합니다.
        return [
            {
                "number": item["number"],
                "title": item["title"],
                "state": item["state"],
                "html_url": item["html_url"],
            }
            for item in response.json()
            if "pull_request" not in item
        ]

    # 새 Issue를 생성합니다.
    def create_issue(self, title: str, body: str) -> dict:
        """GitHub 저장소에 새 Issue를 생성합니다."""

        # 데모 모드이면 실제 생성 없이 예상 결과를 반환합니다.
        if not self.live_mode:
            return {
                "mode": "demo",
                "number": 999,
                "title": title,
                "body": body,
                "html_url": "https://github.com/demo/repository/issues/999",
            }

        # 실제 호출에 필요한 설정을 검사합니다.
        if not all([self.token, self.owner, self.repo]):
            raise RuntimeError("GitHub live 모드 설정이 부족합니다.")

        # Issue 생성 API 주소를 구성합니다.
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/issues"

        # 제목과 본문을 JSON으로 전송합니다.
        response = httpx.post(
            url,
            headers=self._headers(),
            json={"title": title, "body": body},
            timeout=15.0,
        )

        # 실패 응답이면 오류를 발생시킵니다.
        response.raise_for_status()

        # 생성 결과 JSON을 가져옵니다.
        item = response.json()

        # 필요한 필드만 반환합니다.
        return {
            "number": item["number"],
            "title": item["title"],
            "state": item["state"],
            "html_url": item["html_url"],
        }
