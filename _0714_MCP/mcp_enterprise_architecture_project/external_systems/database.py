"""
별도 DB 설치 없이 실행 가능한 SQLite 데이터베이스 어댑터입니다.
"""

# SQLite 데이터베이스를 사용하기 위해 sqlite3를 가져옵니다.
import sqlite3

# DB 파일 경로 타입을 위해 Path를 가져옵니다.
from pathlib import Path


# 데이터베이스 어댑터를 정의합니다.
class DatabaseAdapter:
    """허용된 업무 테이블만 조작하는 안전한 데이터베이스 기능입니다."""

    # SQLite 파일 경로를 전달받습니다.
    def __init__(self, db_file: Path) -> None:
        # DB 파일 경로를 저장합니다.
        self.db_file = db_file

        # DB 상위 폴더가 없으면 생성합니다.
        self.db_file.parent.mkdir(parents=True, exist_ok=True)

        # 예제 테이블을 준비합니다.
        self.initialize()

    # SQLite 연결을 생성합니다.
    def _connect(self) -> sqlite3.Connection:
        """행을 딕셔너리 형태로 조회할 수 있는 연결을 반환합니다."""

        # SQLite 파일에 연결합니다.
        connection = sqlite3.connect(self.db_file)

        # 조회 결과에서 컬럼명으로 접근할 수 있도록 Row 팩토리를 설정합니다.
        connection.row_factory = sqlite3.Row

        # 연결 객체를 반환합니다.
        return connection

    # 업무 메모 테이블을 생성합니다.
    def initialize(self) -> None:
        """예제 업무 메모 테이블을 준비합니다."""

        # 연결 종료를 보장하는 with 문을 사용합니다.
        with self._connect() as connection:
            # 테이블이 없을 때만 생성합니다.
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS work_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    # 업무 메모를 등록합니다.
    def add_note(self, title: str, content: str) -> dict:
        """업무 메모를 안전한 파라미터 바인딩 방식으로 저장합니다."""

        # 연결 종료와 커밋을 보장하는 with 문을 사용합니다.
        with self._connect() as connection:
            # SQL Injection을 방지하기 위해 물음표 바인딩을 사용합니다.
            cursor = connection.execute(
                "INSERT INTO work_notes(title, content) VALUES (?, ?)",
                (title, content),
            )

            # 생성된 ID와 입력 내용을 반환합니다.
            return {"id": cursor.lastrowid, "title": title, "content": content}

    # 최근 업무 메모를 조회합니다.
    def list_notes(self, limit: int = 20) -> list[dict]:
        """최근 업무 메모를 지정한 개수만큼 반환합니다."""

        # 비정상적으로 큰 조회를 막기 위해 범위를 제한합니다.
        safe_limit = max(1, min(limit, 100))

        # 데이터베이스에 연결합니다.
        with self._connect() as connection:
            # 최근 등록된 순서로 데이터를 조회합니다.
            rows = connection.execute(
                "SELECT id, title, content, created_at FROM work_notes ORDER BY id DESC LIMIT ?",
                (safe_limit,),
            ).fetchall()

        # sqlite Row를 일반 딕셔너리 목록으로 변환합니다.
        return [dict(row) for row in rows]

    # 제목과 본문에서 키워드를 검색합니다.
    def search_notes(self, keyword: str, limit: int = 20) -> list[dict]:
        """업무 메모에서 키워드를 검색합니다."""

        # LIKE 검색 패턴을 생성합니다.
        pattern = f"%{keyword}%"

        # 조회 개수를 안전한 범위로 제한합니다.
        safe_limit = max(1, min(limit, 100))

        # 데이터베이스에 연결합니다.
        with self._connect() as connection:
            # 제목 또는 본문이 키워드를 포함하는 행을 조회합니다.
            rows = connection.execute(
                """
                SELECT id, title, content, created_at
                FROM work_notes
                WHERE title LIKE ? OR content LIKE ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (pattern, pattern, safe_limit),
            ).fetchall()

        # 결과를 딕셔너리 목록으로 변환합니다.
        return [dict(row) for row in rows]
