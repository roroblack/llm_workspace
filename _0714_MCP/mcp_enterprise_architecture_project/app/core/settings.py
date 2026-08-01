"""
프로젝트 전체의 환경설정을 관리합니다.
"""

# 반복해서 생성할 필요가 없는 설정 객체를 캐시하기 위해 lru_cache를 가져옵니다.
from functools import lru_cache

# 운영체제와 관계없이 경로를 안전하게 처리하기 위해 Path를 가져옵니다.
from pathlib import Path

# 설정 값의 범위를 검증하기 위해 Field를 가져옵니다.
from pydantic import Field

# .env 파일과 환경변수를 읽기 위해 BaseSettings를 가져옵니다.
from pydantic_settings import BaseSettings, SettingsConfigDict


# 현재 파일의 위치를 기준으로 프로젝트 루트 경로를 계산합니다.
PROJECT_ROOT = Path(__file__).resolve().parents[2]


# 애플리케이션 설정 모델을 정의합니다.
class Settings(BaseSettings):
    """환경변수 값을 타입 안전하게 관리합니다."""

    # FastAPI 화면과 문서에 표시할 애플리케이션 이름입니다.
    app_name: str = "MCP Enterprise Tool Hub"

    # FastAPI 서버가 수신할 호스트 주소입니다.
    app_host: str = "127.0.0.1"

    # FastAPI 서버 포트 번호입니다.
    app_port: int = 8000

    # OpenAI API 키입니다.
    openai_api_key: str = ""

    # OpenAI Responses API에서 사용할 모델 이름입니다.
    openai_model: str = "gpt-4.1-mini"

    # 한 요청에서 OpenAI가 연속으로 실행할 수 있는 MCP Tool 라운드 수입니다.
    openai_max_tool_rounds: int = Field(default=5, ge=1, le=10)

    # 외부 시스템의 실제 API를 호출할지 여부입니다.
    live_mode: bool = False

    # GitHub Personal Access Token입니다.
    github_token: str = ""

    # GitHub 저장소 소유자 이름입니다.
    github_owner: str = ""

    # GitHub 저장소 이름입니다.
    github_repo: str = ""

    # Slack Bot Token입니다.
    slack_bot_token: str = ""

    # Slack 메시지를 전송할 기본 채널 ID입니다.
    slack_channel_id: str = ""

    # SMTP 서버 주소입니다.
    smtp_host: str = ""

    # SMTP 서버 포트입니다.
    smtp_port: int = 587

    # SMTP 로그인 사용자입니다.
    smtp_user: str = ""

    # SMTP 로그인 비밀번호 또는 앱 비밀번호입니다.
    smtp_password: str = ""

    # 이메일 발신 주소입니다.
    email_from: str = ""

    # Browser Tool이 접근할 수 있는 호스트 목록입니다.
    browser_allowed_hosts: str = "example.com,docs.python.org,modelcontextprotocol.io"

    # 파일 Tool이 접근할 수 있는 디렉터리입니다.
    files_dir: Path = PROJECT_ROOT / "data" / "files"

    # Vector Search 원본 문서 디렉터리입니다.
    vector_docs_dir: Path = PROJECT_ROOT / "data" / "vector_docs"

    # Vector Search 인덱스 파일 경로입니다.
    vector_index_file: Path = PROJECT_ROOT / "data" / "vector_index.json"

    # SQLite 데이터베이스 파일 경로입니다.
    sqlite_file: Path = PROJECT_ROOT / "data" / "enterprise.db"

    # Calendar Tool이 저장할 JSON 파일 경로입니다.
    calendar_file: Path = PROJECT_ROOT / "data" / "calendar" / "events.json"

    # MCP 서버 모듈 실행 이름입니다.
    mcp_server_module: str = "mcp_server.server"

    # .env 파일을 읽는 방법을 정의합니다.
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 허용된 Browser Tool 호스트를 리스트로 반환합니다.
    def allowed_browser_hosts(self) -> list[str]:
        """쉼표로 구분된 호스트 문자열을 정리하여 반환합니다."""

        # 각 문자열의 공백을 제거하고 비어 있지 않은 항목만 반환합니다.
        return [item.strip().lower() for item in self.browser_allowed_hosts.split(",") if item.strip()]


# 동일한 Settings 객체를 재사용하도록 캐시합니다.
@lru_cache
def get_settings() -> Settings:
    """프로젝트 전역에서 사용할 설정 객체를 반환합니다."""

    # Settings 객체를 생성하여 반환합니다.
    return Settings()
