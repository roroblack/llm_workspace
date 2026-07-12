"""헬스 체크 라우터.

/api/health 는 LLM/네트워크 실호출 없이 '설정·키·경로 존재 여부'만 boolean으로
보고한다 (Codex 합의).
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "provider": settings.LLM_PROVIDER,
        "readiness": settings.readiness(),
    }
