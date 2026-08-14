"""TEST-OPS-READY-001 — 기동/데이터 분리 readiness (REQ-OPS-01)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.obs import readiness


def test_readiness_reports_expected_fields():
    s = readiness.check_readiness()
    for key in ("ready", "db_tables_ready", "missing_tables", "vector_index_ready", "hint"):
        assert key in s


def test_readiness_not_ready_when_index_missing(monkeypatch, tmp_path):
    # 인덱스 없는 빈 디렉터리를 가리키면 vector_index_ready=False → ready=False, hint 제공(무폴백: 명시적)
    fake_settings = SimpleNamespace(
        VECTOR_DIR=tmp_path,
        DATABASE_URL=f"sqlite:///{tmp_path / 'missing.sqlite3'}",
        SQLITE_LEGACY_ENABLED=False,
        AUTH_PERSISTENCE="postgres",
        OPS_PERSISTENCE="postgres",
    )
    monkeypatch.setattr(readiness, "get_settings", lambda: fake_settings)
    s = readiness.check_readiness()
    assert s["vector_index_ready"] is False
    assert s["ready"] is False
    assert s["hint"]  # 준비 방법 안내


def test_readiness_endpoint(client):
    r = client.get("/api/health/ready")
    assert r.status_code == 200
    body = r.json()
    assert "ready" in body
    assert "components" in body
    for sensitive in (
        "missing_tables",
        "reason",
        "database",
        "schema",
        "hint",
        "details",
    ):
        assert sensitive not in r.text


def test_public_readiness_keeps_only_boolean_health(monkeypatch):
    monkeypatch.setattr(
        readiness,
        "check_readiness",
        lambda: {
            "ready": False,
            "db_tables_ready": False,
            "missing_tables": ["secret_table"],
            "vector_index_ready": True,
            "hint": "postgresql://runtime:secret@db.internal/insurance",
            "clause_index": {"required": True, "ready": False, "reason": "secret"},
            "candidate_fact_sources": {"ready": True, "details": ["private"]},
            "demo_store": {"ready": False, "reason": "db.internal"},
        },
    )

    public = readiness.public_readiness()

    assert public["ready"] is False
    assert public["components"]["clause_index"] is False
    rendered = str(public)
    assert "secret" not in rendered
    assert "db.internal" not in rendered


def test_missing_sqlite_is_not_created(tmp_path):
    path = tmp_path / "missing.sqlite3"
    settings = SimpleNamespace(
        DATABASE_URL=f"sqlite:///{path.as_posix()}",
        SQLITE_LEGACY_ENABLED=True,
    )

    existing = readiness._existing_sqlite_tables(settings, ("users",))

    assert existing == set()
    assert not path.exists()


def test_sqlite_readiness_uses_read_only_connection(monkeypatch, tmp_path):
    path = tmp_path / "legacy.sqlite3"
    with readiness.sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE users (id integer primary key)")
    real_connect = readiness.sqlite3.connect
    captured: dict[str, object] = {}

    def checked_connect(database, *args, **kwargs):
        captured.update(database=database, **kwargs)
        return real_connect(database, *args, **kwargs)

    monkeypatch.setattr(readiness.sqlite3, "connect", checked_connect)
    settings = SimpleNamespace(
        DATABASE_URL=f"sqlite:///{path.as_posix()}",
        SQLITE_LEGACY_ENABLED=True,
    )

    existing = readiness._existing_sqlite_tables(settings, ("users",))

    assert existing == {"users"}
    assert captured["uri"] is True
    assert "mode=ro" in str(captured["database"])


def test_file_clause_store_skips_postgres_probe(monkeypatch):
    from app import composition

    monkeypatch.setattr(composition, "_clause_store_kind", lambda: "file")
    monkeypatch.setattr(
        readiness,
        "_clause_index_state",
        lambda: pytest.fail("file clause store must not probe PostgreSQL"),
    )

    result = readiness.check_readiness()

    assert result["clause_index"] == {
        "backend": "file",
        "checked": False,
        "required": False,
    }
