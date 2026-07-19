"""Phase 1 — 모델 레지스트리 스키마·하드코딩 스캔.

REQ-LLM-REG-01: TEST-LLM-REG-001(스키마 검증). REQ-LLM-REG-02: TEST-LLM-REG-002(신 코드 하드코딩 모델ID 0).
"""

from __future__ import annotations

import pathlib
import re

import pytest

from app.core.errors import ConfigError
from app.core.model_registry import ModelProfile, get_active_profile, load_registry

_APP = pathlib.Path(__file__).resolve().parents[1] / "app"


def test_llm_reg_001_registry_loads_and_validates():
    reg = load_registry()
    assert reg, "레지스트리에 최소 1개 프로필"
    for p in reg.values():
        assert p.provider_model_id and "latest" not in p.provider_model_id.lower()
        assert p.provider and p.runtime


def test_llm_reg_001_rejects_latest_alias():
    with pytest.raises(Exception):
        ModelProfile(profile_id="x", provider="local", provider_model_id="gemma-latest", runtime="llama-cpp-python")


def test_llm_reg_001_rejects_empty_model_id():
    with pytest.raises(Exception):
        ModelProfile(profile_id="x", provider="local", provider_model_id="  ", runtime="rt")


def test_active_profile_resolves():
    p = get_active_profile()
    assert p.profile_id  # 기본 ACTIVE_MODEL_PROFILE이 레지스트리에 존재


def test_unknown_active_profile_raises(monkeypatch):
    from app.core import model_registry as mr

    monkeypatch.setattr(mr, "load_registry", lambda path=None: {})
    with pytest.raises(ConfigError):
        get_active_profile()


def test_verified_flag():
    # 현재 프로필은 checksum/verified_at이 null → verified=False
    for p in load_registry().values():
        assert p.verified == bool(p.artifact_sha256 and p.verified_at)


# 알려진 모델 ID 패턴(신 Clean Arch 코드에 소스 하드코딩 금지 — 레지스트리로 해석해야 함)
_MODEL_ID_PATTERNS = [
    r"gpt-\d", r"gpt-4", r"gpt-5", r"gemini-\d", r"gemma-\d",
    r"qwen[\d.]", r"claude-", r"\bo1-", r"\bo3-", r"koelectra",
]
# 신 Clean Arch 계층만 검사(레거시 app/core/config.py 등은 이후 Phase에서 수렴)
_NEW_CODE_DIRS = [_APP / "application", _APP / "adapters"]


def test_llm_reg_002_no_hardcoded_model_ids_in_new_code():
    offenders: list[str] = []
    for root in _NEW_CODE_DIRS:
        for py in root.rglob("*.py"):
            text = py.read_text(encoding="utf-8")
            for pat in _MODEL_ID_PATTERNS:
                for m in re.finditer(pat, text, re.IGNORECASE):
                    offenders.append(f"{py.name}: '{m.group(0)}'")
    assert offenders == [], f"신 코드에 하드코딩 모델ID: {offenders}"
