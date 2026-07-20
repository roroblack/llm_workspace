# -*- coding: utf-8 -*-
"""생성된 최종 리포트를 MySQL REPORT 테이블에 저장합니다."""

from datetime import datetime, timezone
from typing import Any

from app.core.settings import get_settings


def _normalize_result_time(value: object | None) -> datetime:
    """ISO 문자열 또는 datetime을 MySQL DATETIME용 UTC naive 값으로 변환합니다."""
    if value is None or value == "":
        parsed = datetime.now(timezone.utc)
    elif isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        normalized = value.strip()
        if normalized.endswith("Z"):
            normalized = f"{normalized[:-1]}+00:00"
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise ValueError("result_time은 ISO 8601 날짜·시간이어야 합니다.") from exc
    else:
        raise ValueError("result_time은 ISO 8601 문자열 또는 datetime이어야 합니다.")

    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def _connect() -> Any:
    """환경 설정으로 MySQL 연결을 생성합니다."""
    try:
        import pymysql
    except ImportError as exc:
        raise RuntimeError("MySQL 저장을 사용하려면 PyMySQL을 설치해야 합니다.") from exc

    settings = get_settings()
    return pymysql.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        database=settings.mysql_database,
        charset="utf8mb4",
        connect_timeout=settings.mysql_connect_timeout,
        autocommit=False,
    )


def save_report_to_mysql(
    topic: object,
    result: object,
    result_time: object | None = None,
) -> dict[str, object]:
    """REPORT 테이블을 준비하고 최종 답변 한 건을 안전하게 저장합니다."""
    clean_topic = str(topic).strip()
    clean_result = str(result).strip()
    if not clean_topic:
        raise ValueError("저장할 리포트 주제(topic)가 필요합니다.")
    if not clean_result:
        raise ValueError("저장할 최종 답변(result)이 필요합니다.")

    completed_at = _normalize_result_time(result_time)
    connection = _connect()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS `REPORT` (
                    `TOPIC` VARCHAR(3000) NOT NULL,
                    `RESULT` LONGTEXT NOT NULL,
                    `RESULT_TIME` DATETIME(6) NOT NULL
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """
            )
            cursor.execute(
                """
                INSERT INTO `REPORT` (`TOPIC`, `RESULT`, `RESULT_TIME`)
                VALUES (%s, %s, %s)
                """,
                (clean_topic, clean_result, completed_at),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return {
        "saved": True,
        "table": "REPORT",
        "topic": clean_topic,
        "result_time": completed_at.isoformat(timespec="microseconds") + "Z",
    }
