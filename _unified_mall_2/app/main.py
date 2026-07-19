"""FastAPI 진입점.

앱 조립: trace 미들웨어 + 예외 핸들러 + 전 라우터 + 정적 UI. 기동 시 자동 DB/인덱스 설정은
하지 않는다(REQ-OPS-01) — 명시적 `scripts.manage`로 준비하고 `/api/health/ready`로 확인한다.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.errors import register_exception_handlers
from app.obs.trace import TraceMiddleware
from app.routers import (
    agent,
    auth,
    health,
    lab,
    mcp,
    nlp,
    orders,
    payments,
    products,
    rag,
    workflow,
)

_STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # 기동 시 자동 create_all/seed/index를 하지 않는다(REQ-OPS-01, Phase 2).
    # 데이터 준비는 명시적 명령으로: `python -m scripts.manage migrate|seed|ingest`.
    # 준비 상태는 GET /api/health/ready 로 확인(미준비 시 명시적으로 알림, 무폴백).
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="승승장구몰 AI 커머스 에이전트",
        version="0.3.0",
        lifespan=lifespan,
    )
    app.add_middleware(TraceMiddleware)  # 요청별 trace_id + X-Trace-ID 응답 헤더
    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(products.router)
    app.include_router(orders.router)
    app.include_router(payments.router)
    app.include_router(agent.router)
    app.include_router(rag.router)
    app.include_router(nlp.router)
    app.include_router(lab.router)
    app.include_router(mcp.router)
    app.include_router(workflow.router)

    # 정적 UI
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(str(_STATIC_DIR / "index.html"))

    return app


app = create_app()
