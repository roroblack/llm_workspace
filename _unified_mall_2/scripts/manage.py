"""명시적 운영 명령(REQ-OPS-01) — 기동 시 자동설정을 대체.

사용:
    python -m scripts.manage migrate   # 테이블 생성(멱등)
    python -m scripts.manage seed      # 상품 시딩(멱등)
    python -m scripts.manage ingest    # RAG 인덱스 빌드(없거나 stale일 때)
    python -m scripts.manage ready      # readiness 상태 출력

무폴백: 각 명령은 성공/실패를 명확히 보고하며, 실패를 삼키지 않는다.
"""

from __future__ import annotations

import argparse
import json
import sys


def cmd_migrate() -> None:
    from app.db.database import Base, engine

    # 모든 모델이 Base에 등록되도록 import
    import app.db.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    print("[migrate] 테이블 생성 완료(멱등).")


def cmd_seed() -> None:
    from app.db.database import SessionLocal
    from app.db.seed import seed_products

    db = SessionLocal()
    try:
        result = seed_products(db)
    finally:
        db.close()
    print(f"[seed] 완료: {result}")


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


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="운영 관리 명령")
    parser.add_argument("command", choices=["migrate", "seed", "ingest", "ready"])
    args = parser.parse_args(argv)
    {"migrate": cmd_migrate, "seed": cmd_seed, "ingest": cmd_ingest, "ready": cmd_ready}[
        args.command
    ]()


if __name__ == "__main__":
    main()
