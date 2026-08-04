"""명시적 운영 명령(REQ-OPS-01) — 기동 시 자동설정을 대체.

사용:
    python -m scripts.manage migrate   # 테이블 생성(멱등)
    python -m scripts.manage ingest    # RAG 인덱스 빌드(없거나 stale일 때)
    python -m scripts.manage ready      # readiness 상태 출력

무폴백: 각 명령은 성공/실패를 명확히 보고하며, 실패를 삼키지 않는다.
"""

from __future__ import annotations

import argparse
import json
import sys


def _add_missing_columns(engine) -> list[str]:
    """기존 테이블에 빠진 컬럼을 멱등하게 추가한다.

    `create_all`은 **없는 테이블만** 만들고 기존 테이블에 컬럼을 추가하지 않는다. 그래서
    Phase 9의 `users.role`처럼 나중에 생긴 컬럼은 기존 DB에 반영되지 않아 조용히 깨진다.
    Alembic 없이 가는 대신 여기서 명시적으로 추가하고, 아래에서 **사후 검증**한다.
    """
    from sqlalchemy import inspect, text

    added: list[str] = []
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return added  # create_all이 새로 만들었으면 스키마가 이미 최신
    columns = {c["name"] for c in inspector.get_columns("users")}
    if "role" not in columns:
        with engine.begin() as conn:
            # 기존 사용자는 전부 USER. 관리자 자동 승격은 하지 않는다.
            conn.execute(
                text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'USER'")
            )
            conn.execute(text("UPDATE users SET role = 'USER' WHERE role IS NULL"))
        added.append("users.role")
    return added


def _verify_schema(engine) -> None:
    """마이그레이션 사후 검증 — 기대 컬럼이 실제로 있는지 확인하고, 없으면 명시적 실패."""
    from sqlalchemy import inspect

    from app.core.errors import InfraError

    inspector = inspect(engine)
    columns = {c["name"] for c in inspector.get_columns("users")}
    if "role" not in columns:
        raise InfraError("마이그레이션 후에도 users.role 컬럼이 없습니다(스키마 검증 실패).")


def cmd_migrate() -> None:
    from app.db.database import Base, engine

    # 모든 모델이 Base에 등록되도록 import
    import app.db.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    added = _add_missing_columns(engine)
    _verify_schema(engine)
    if added:
        print(f"[migrate] 컬럼 추가: {', '.join(added)}")
    print("[migrate] 테이블 생성·스키마 검증 완료(멱등).")


def cmd_ingest() -> None:
    from app.rag.build_index import build_index, index_is_current

    if index_is_current():
        print("[ingest] 인덱스가 최신 상태 — 건너뜀.")
        return
    build_index()
    print("[ingest] RAG 인덱스 빌드 완료.")


def cmd_ready() -> None:
    from app.obs.readiness import check_readiness

    status = check_readiness()
    print(json.dumps(status, ensure_ascii=False, indent=2))
    if not status["ready"]:
        sys.exit(1)  # 미준비는 비정상 종료(무폴백)


def set_role(username: str, role: str) -> str:
    """사용자 역할을 변경한다(멱등). **규칙은 `app.auth.roles.change_role` 한 벌뿐이다.**

    ★전에는 이 함수가 규칙(마지막 관리자 강등 금지·감사 기록)을 **직접** 들고 있었다.
      그러다 관리자 화면에서도 역할을 바꾸게 되면서 규칙이 두 곳이 될 뻔했다 —
      두 곳이면 느슨한 쪽이 실질 규칙이 된다. 그래서 도메인으로 옮기고 여기서는 부른다.

    부트스트랩은 여전히 **이 CLI 하나뿐**이다. 최초 관리자를 화면에서 만들 수 있게 하면
    가입한 누구나 관리자가 된다(권한 상승). 그 뒤의 추가는 관리자가 화면에서 한다.
    """
    from app.auth.roles import change_role
    from app.db.database import SessionLocal

    db = SessionLocal()
    try:
        return change_role(db, username, role, actor="cli")["message"]
    finally:
        db.close()


def cmd_promote(username: str) -> None:
    from app.auth.roles import ROLE_ADMIN

    print(f"[promote] {set_role(username, ROLE_ADMIN)}")


def cmd_demote(username: str) -> None:
    from app.auth.roles import ROLE_USER

    print(f"[demote] {set_role(username, ROLE_USER)}")


def purge_gaps(days: int) -> int:
    """보존기간이 지난 지식보강 큐 항목을 파기한다. 삭제 건수를 반환."""
    from datetime import datetime, timedelta

    from app.db.database import SessionLocal
    from app.db.models import KnowledgeGap

    cutoff = datetime.utcnow() - timedelta(days=days)
    db = SessionLocal()
    try:
        deleted = (
            db.query(KnowledgeGap)
            .filter(KnowledgeGap.created_at < cutoff)
            .delete(synchronize_session=False)
        )
        db.commit()
        return deleted
    finally:
        db.close()


def cmd_purge_gaps(days: int) -> None:
    print(f"[purge-gaps] {purge_gaps(days)}건 파기(보존 {days}일).")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="운영 관리 명령")
    parser.add_argument(
        "command",
        choices=["migrate", "ingest", "ready", "promote", "demote", "purge-gaps"],
    )
    parser.add_argument("target", nargs="?", help="promote/demote의 username")
    parser.add_argument("--days", type=int, default=90, help="purge-gaps 보존기간(일)")
    args = parser.parse_args(argv)

    if args.command in ("promote", "demote"):
        if not args.target:
            parser.error(f"{args.command}에는 username이 필요합니다.")
        (cmd_promote if args.command == "promote" else cmd_demote)(args.target)
        return
    if args.command == "purge-gaps":
        cmd_purge_gaps(args.days)
        return
    {"migrate": cmd_migrate, "ingest": cmd_ingest, "ready": cmd_ready}[
        args.command
    ]()


if __name__ == "__main__":
    main()
