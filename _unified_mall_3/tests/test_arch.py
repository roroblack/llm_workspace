"""TEST-ARCH-001 — Application 계층 프레임워크 무-import 검사(정적 스캔).

v3.2 §2 의존성 규칙: app/application/*는 FastAPI/LangChain/SQLAlchemy/openai를 import하지 않는다.
"""

from __future__ import annotations

import pathlib
import re

_APP_DIR = pathlib.Path(__file__).resolve().parents[1] / "app" / "application"
_FORBIDDEN = ("fastapi", "langchain", "sqlalchemy", "openai")


def _import_lines(text: str) -> list[str]:
    lines = []
    for raw in text.splitlines():
        s = raw.strip()
        if s.startswith("import ") or s.startswith("from "):
            lines.append(s)
    return lines


def test_arch_001_application_has_no_framework_imports():
    offenders: list[str] = []
    for py in _APP_DIR.rglob("*.py"):
        for line in _import_lines(py.read_text(encoding="utf-8")):
            for fb in _FORBIDDEN:
                if re.search(rf"\b{fb}\b", line):
                    offenders.append(f"{py.name}: {line}")
    assert offenders == [], f"Application 계층 금지 import 발견: {offenders}"


def test_application_package_exists():
    assert (_APP_DIR / "ports.py").exists()
    assert (_APP_DIR / "answer_question.py").exists()


# ── TEST-ARCH-002 — 클린아키텍처 2단계 경계 ────────────────────────────────
# 안쪽(app/core/{domain,ports,usecases})은 프레임워크도, 바깥 계층도 모른다.
# 경계를 하나만 두는 대신 그 하나는 절대 넘지 않는다.

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_INNER_DIRS = (
    _ROOT / "app" / "core" / "domain",
    _ROOT / "app" / "core" / "ports",
    _ROOT / "app" / "core" / "usecases",
)
#: 안쪽에서 import 하면 안 되는 바깥 패키지. 의존 방향은 항상 안쪽으로만.
_OUTER_PACKAGES = (
    "app.outer",
    "app.adapters",
    "app.routers",
    "app.db",
    "app.rag",
    "app.services",
    "app.mcp",
    "app.a2a",
)


def _scan_inner() -> list[tuple[pathlib.Path, str]]:
    found: list[tuple[pathlib.Path, str]] = []
    for d in _INNER_DIRS:
        if not d.exists():
            continue
        for py in d.rglob("*.py"):
            for line in _import_lines(py.read_text(encoding="utf-8")):
                found.append((py, line))
    return found


def test_arch_002_inner_layer_exists():
    missing = [str(d.relative_to(_ROOT)) for d in _INNER_DIRS if not d.exists()]
    assert missing == [], f"안쪽 계층 디렉터리 누락: {missing}"


def test_arch_002_inner_layer_has_no_framework_imports():
    offenders = [
        f"{py.relative_to(_ROOT)}: {line}"
        for py, line in _scan_inner()
        for fb in _FORBIDDEN
        if re.search(rf"\b{fb}\b", line)
    ]
    assert offenders == [], f"안쪽 계층 금지 import 발견: {offenders}"


def test_arch_002_inner_layer_does_not_import_outer():
    offenders = [
        f"{py.relative_to(_ROOT)}: {line}"
        for py, line in _scan_inner()
        for pkg in _OUTER_PACKAGES
        if re.search(rf"\b{re.escape(pkg)}\b", line)
    ]
    assert offenders == [], f"안쪽 계층이 바깥을 참조합니다(의존 방향 역전): {offenders}"
