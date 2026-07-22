# -*- coding: utf-8 -*-
"""실행성 고객 문의를 판별하고 MySQL 담당 부서 큐에 저장합니다."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from app.core.logging_config import setup_logging
from app.core.settings import get_settings

logger = setup_logging()

HANDOFF_ANSWER = "담당 부서로 연결해 드리겠습니다."

_SUBJECT_KEYWORDS = ("교환", "환불", "반품")
_ACTION_KEYWORDS = (
    "해주세요",
    "해 주세요",
    "해줘",
    "원해요",
    "원합니다",
    "신청",
    "접수",
    "요청",
    "처리",
    "하고 싶",
    "바꿔",
    "돌려",
)
_INFORMATION_KEYWORDS = ("방법", "절차", "정책", "조건", "기간", "가능", "어떻게", "알려")


def is_action_complaint(message: str) -> bool:
    """교환·환불·반품을 실제로 처리해 달라는 요청인지 결정적으로 판별합니다."""
    normalized = re.sub(r"\s+", " ", message.strip().lower())
    if not any(keyword in normalized for keyword in _SUBJECT_KEYWORDS):
        return False
    if any(keyword in normalized for keyword in _INFORMATION_KEYWORDS):
        return False
    return any(keyword in normalized for keyword in _ACTION_KEYWORDS)


def infer_department(message: str) -> str:
    """문의 내용에 맞는 담당 부서 식별자를 반환합니다."""
    normalized = message.lower()
    if "환불" in normalized:
        return "CS_REFUND"
    if "교환" in normalized:
        return "CS_EXCHANGE"
    if "반품" in normalized:
        return "CS_RETURN"
    return "CS_GENERAL"


def _validate_database_name(value: str) -> str:
    """SQL 식별자로 안전한 데이터베이스 이름만 허용합니다."""
    if not re.fullmatch(r"[A-Za-z0-9_]+", value):
        raise ValueError("MYSQL_DATABASE는 영문, 숫자, 밑줄만 사용할 수 있습니다.")
    return value


def _connect(database: str | None = None) -> Any:
    """환경설정으로 PyMySQL 연결을 만듭니다."""
    try:
        import pymysql
    except ImportError as exc:
        raise RuntimeError("고객 문의 저장을 사용하려면 PyMySQL을 설치해야 합니다.") from exc

    settings = get_settings()
    kwargs: dict[str, object] = {
        "host": settings.mysql_host,
        "port": settings.mysql_port,
        "user": settings.mysql_user,
        "password": settings.mysql_password,
        "charset": "utf8mb4",
        "connect_timeout": settings.mysql_connect_timeout,
        "autocommit": False,
    }
    if database:
        kwargs["database"] = database
    return pymysql.connect(**kwargs)


def ensure_complaint_table() -> None:
    """fastapi_db와 customer_complaint 테이블을 준비합니다."""
    settings = get_settings()
    database = _validate_database_name(settings.mysql_database)
    # 기존 fastapi_db에 바로 연결하면 제한된 운영 계정에도 불필요한 CREATE DATABASE 권한을 요구하지 않습니다.
    try:
        connection = _connect(database)
    except Exception as exc:
        # MySQL 1049(Unknown database)일 때만 서버 수준 연결로 데이터베이스를 생성합니다.
        error_code = exc.args[0] if getattr(exc, "args", ()) else None
        if error_code != 1049:
            raise
        bootstrap = _connect()
        try:
            with bootstrap.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{database}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            bootstrap.commit()
        except Exception:
            bootstrap.rollback()
            raise
        finally:
            bootstrap.close()
        connection = _connect(database)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS `customer_complaint` (
                    `cc_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
                    `custum_id` VARCHAR(100) NOT NULL,
                    `dept_id` VARCHAR(50) NOT NULL,
                    `message` TEXT NOT NULL,
                    `receipt_status` TINYINT(1) NOT NULL DEFAULT 0,
                    `resolution_status` TINYINT(1) NOT NULL DEFAULT 0,
                    `inquiry_date` DATETIME(6) NOT NULL,
                    `receipt_date` DATETIME(6) NULL,
                    `resolution_date` DATETIME(6) NULL,
                    PRIMARY KEY (`cc_id`),
                    INDEX `ix_customer_complaint_customer` (`custum_id`),
                    INDEX `ix_customer_complaint_department_status`
                        (`dept_id`, `receipt_status`, `resolution_status`)
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def create_customer_complaint(
    custum_id: str,
    message: str,
    dept_id: str | None = None,
) -> dict[str, object]:
    """문의 한 건을 미접수·미처리 상태로 저장하고 생성 정보를 반환합니다."""
    clean_customer = custum_id.strip()
    clean_message = message.strip()
    clean_department = (dept_id or infer_department(clean_message)).strip()
    if not clean_customer:
        raise ValueError("고객아이디(custum_id)가 필요합니다.")
    if not clean_message:
        raise ValueError("문의 내용(message)이 필요합니다.")
    if not clean_department:
        raise ValueError("담당부서아이디(dept_id)가 필요합니다.")

    ensure_complaint_table()
    inquiry_date = datetime.now()
    connection = _connect(get_settings().mysql_database)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO `customer_complaint` (
                    `custum_id`, `dept_id`, `message`,
                    `receipt_status`, `resolution_status`,
                    `inquiry_date`, `receipt_date`, `resolution_date`
                ) VALUES (%s, %s, %s, 0, 0, %s, NULL, NULL)
                """,
                (clean_customer, clean_department, clean_message, inquiry_date),
            )
            cc_id = int(cursor.lastrowid)
        connection.commit()
    except Exception:
        connection.rollback()
        logger.exception("고객 문의 MySQL 저장 실패: custum_id=%s dept_id=%s", clean_customer, clean_department)
        raise
    finally:
        connection.close()

    logger.info("고객 문의 저장 완료: cc_id=%s custum_id=%s dept_id=%s", cc_id, clean_customer, clean_department)
    return {
        "answer": HANDOFF_ANSWER,
        "cc_id": cc_id,
        "custum_id": clean_customer,
        "dept_id": clean_department,
        "receipt_status": False,
        "resolution_status": False,
        "inquiry_date": inquiry_date.isoformat(timespec="microseconds"),
    }
