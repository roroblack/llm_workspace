# -*- coding: utf-8 -*-
"""외부 MySQL 없이 REPORT 저장 SQL을 검증하는 단위 테스트입니다."""

from datetime import datetime

import pytest

from app.services import mysql_service


class FakeCursor:
    """실행된 SQL과 파라미터를 기록하는 가짜 커서입니다."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, object | None]] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> bool:
        return False

    def execute(self, sql: str, params: object | None = None) -> None:
        self.calls.append((sql, params))


class FakeConnection:
    """트랜잭션 완료 여부를 기록하는 가짜 MySQL 연결입니다."""

    def __init__(self) -> None:
        self.cursor_instance = FakeCursor()
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self) -> FakeCursor:
        return self.cursor_instance

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def close(self) -> None:
        self.closed = True


def test_save_report_creates_table_and_inserts_with_parameters(monkeypatch) -> None:
    """REPORT 생성 후 사용자 값을 바인딩 파라미터로 INSERT하는지 검사합니다."""
    connection = FakeConnection()
    monkeypatch.setattr(mysql_service, "_connect", lambda: connection)

    saved = mysql_service.save_report_to_mysql(
        "무선이어버드 시장",
        "최종 답변",
        "2026-07-20T08:30:45.123456Z",
    )

    assert connection.committed is True
    assert connection.rolled_back is False
    assert connection.closed is True
    assert len(connection.cursor_instance.calls) == 2
    create_sql, create_params = connection.cursor_instance.calls[0]
    insert_sql, insert_params = connection.cursor_instance.calls[1]
    assert "CREATE TABLE IF NOT EXISTS `REPORT`" in create_sql
    assert create_params is None
    assert "VALUES (%s, %s, %s)" in insert_sql
    assert insert_params == (
        "무선이어버드 시장",
        "최종 답변",
        datetime(2026, 7, 20, 8, 30, 45, 123456),
    )
    assert saved["saved"] is True
    assert saved["table"] == "REPORT"


def test_save_report_rejects_invalid_time_before_connect(monkeypatch) -> None:
    """잘못된 완료 시각은 DB 연결 전에 거부하는지 검사합니다."""
    monkeypatch.setattr(
        mysql_service,
        "_connect",
        lambda: pytest.fail("잘못된 입력에서는 DB에 연결하면 안 됩니다."),
    )

    with pytest.raises(ValueError, match="ISO 8601"):
        mysql_service.save_report_to_mysql("주제", "답변", "not-a-date")
