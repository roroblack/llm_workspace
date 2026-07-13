# -*- coding: utf-8 -*-
"""프로젝트 상태 확인용 API 라우터입니다."""

# FastAPI 라우터 클래스를 불러옵니다.
from fastapi import APIRouter

# 환경 상태 확인 함수를 불러옵니다.
from app.common import get_env_status

# /api/system 경로 아래에 API를 묶기 위한 라우터를 생성합니다.
router = APIRouter(prefix="/api/system", tags=["시스템 확인"])


@router.get("/health")
def health_check():
    """FastAPI 서버가 정상 동작 중인지 확인합니다."""

    return {
        "status": "ok",
        "message": "FastAPI LLM 실습 테스트 앱이 실행 중입니다.",
    }


@router.get("/env")
def env_check():
    """API Key와 프로젝트 경로 설정 상태를 확인합니다."""

    return get_env_status()
