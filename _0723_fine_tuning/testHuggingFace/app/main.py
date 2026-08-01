"""FastAPI 진입점.

실행:
    .\\.venv\\Scripts\\Activate.ps1
    uvicorn app.main:app --reload
    -> http://127.0.0.1:8000/docs
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.core.config import get_settings
from app.core.hf.pipelines import ALL_TASKS, registry
from app.models.schemas import HealthResponse
from app.routers import nlp_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if settings.hf_home:
        # transformers 가 임포트 시점 이후에도 참조하는 캐시 경로
        os.environ.setdefault("HF_HOME", settings.hf_home)

    tasks = settings.preload_tasks(ALL_TASKS)
    if tasks:
        logger.info(
            "모델 프리로딩 시작: %s (최초 실행 시 다운로드로 수 분 걸릴 수 있음)",
            ", ".join(tasks),
        )
        registry.preload(tasks)
        logger.info("모델 프리로딩 완료: %s", ", ".join(tasks))
        lazy = [t for t in ALL_TASKS if t not in tasks]
        if lazy:
            logger.info("나머지는 lazy 로딩: %s", ", ".join(lazy))
    else:
        logger.info("lazy 로딩 모드 — 각 엔드포인트 첫 요청 때 모델을 로딩한다.")

    yield
    logger.info("애플리케이션 종료")


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    description=(
        "HuggingFace Transformers `pipeline` 을 FastAPI 로 감싼 추론 서비스.\n\n"
        "**엔드포인트**\n"
        "- `POST /nlp/classify` — 감성분석 (단건/배치)\n"
        "- `POST /nlp/summarize` — 추상적 요약 (긴 문서 자동 분할)\n"
        "- `POST /nlp/translate` — 번역 (기본 영→한)\n\n"
        "**주의**: 모델은 프로세스당 1회만 로딩되는 싱글톤이다. "
        "첫 요청은 모델 다운로드 때문에 느릴 수 있고, 이후 요청은 빠르다. "
        "현재 로딩 상태는 `GET /health` 에서 확인한다."
    ),
)

app.include_router(nlp_router.router)


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="헬스체크 및 모델 로딩 상태",
)
def health() -> HealthResponse:
    s = get_settings()
    return HealthResponse(
        status="ok",
        app=s.app_name,
        version=s.app_version,
        device="cpu" if s.device < 0 else f"cuda:{s.device}",
        pipelines=registry.status(),
    )
