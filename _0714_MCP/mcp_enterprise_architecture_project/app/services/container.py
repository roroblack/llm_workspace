"""
외부 시스템 어댑터를 한 곳에서 생성하고 공유합니다.
"""

# 동일한 Container를 재사용하기 위해 lru_cache를 가져옵니다.
from functools import lru_cache

# 설정 객체를 가져옵니다.
from app.core.settings import get_settings

# 각 외부 시스템 어댑터를 가져옵니다.
from external_systems.browser import BrowserAdapter
from external_systems.calendar_store import CalendarAdapter
from external_systems.database import DatabaseAdapter
from external_systems.email_sender import EmailAdapter
from external_systems.file_system import FileSystemAdapter
from external_systems.github_api import GitHubAdapter
from external_systems.python_sandbox import PythonSandboxAdapter
from external_systems.slack_api import SlackAdapter
from external_systems.vector_store import VectorSearchAdapter


# 서비스 Container를 정의합니다.
class Container:
    """프로젝트의 모든 외부 시스템 어댑터를 생성합니다."""

    # 설정을 읽고 각 어댑터를 초기화합니다.
    def __init__(self) -> None:
        # 공용 설정 객체를 가져옵니다.
        self.settings = get_settings()

        # 파일 시스템 어댑터를 생성합니다.
        self.files = FileSystemAdapter(self.settings.files_dir)

        # SQLite 데이터베이스 어댑터를 생성합니다.
        self.database = DatabaseAdapter(self.settings.sqlite_file)

        # GitHub 어댑터를 생성합니다.
        self.github = GitHubAdapter(
            live_mode=self.settings.live_mode,
            token=self.settings.github_token,
            owner=self.settings.github_owner,
            repo=self.settings.github_repo,
        )

        # Slack 어댑터를 생성합니다.
        self.slack = SlackAdapter(
            live_mode=self.settings.live_mode,
            token=self.settings.slack_bot_token,
            default_channel=self.settings.slack_channel_id,
        )

        # 허용 목록 기반 Browser 어댑터를 생성합니다.
        self.browser = BrowserAdapter(self.settings.allowed_browser_hosts())

        # 로컬 캘린더 어댑터를 생성합니다.
        self.calendar = CalendarAdapter(self.settings.calendar_file)

        # SMTP 이메일 어댑터를 생성합니다.
        self.email = EmailAdapter(
            live_mode=self.settings.live_mode,
            host=self.settings.smtp_host,
            port=self.settings.smtp_port,
            user=self.settings.smtp_user,
            password=self.settings.smtp_password,
            email_from=self.settings.email_from,
        )

        # 로컬 Vector Search 어댑터를 생성합니다.
        self.vector = VectorSearchAdapter(
            docs_dir=self.settings.vector_docs_dir,
            index_file=self.settings.vector_index_file,
        )

        # 안전한 산술 전용 Python 어댑터를 생성합니다.
        self.python = PythonSandboxAdapter()


# Container를 한 번만 생성하도록 캐시합니다.
@lru_cache
def get_container() -> Container:
    """공용 Container 객체를 반환합니다."""

    # Container를 생성하여 반환합니다.
    return Container()
