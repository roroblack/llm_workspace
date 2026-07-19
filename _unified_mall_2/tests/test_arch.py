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
