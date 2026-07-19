"""FastAPI 진입점.

Phase 1: 예외 핸들러 + health.
Phase 2: DB 테이블 생성 + 시딩 + auth/products/orders/payments 라우터.
정적 UI/에이전트 라우터는 이후 Phase에서 붙인다.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.errors import register_exception_handlers
from app.db.database import Base, SessionLocal, engine
from app.db.seed import seed_products
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
    # 테이블 생성 + 시딩 (멱등)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_products(db)
    finally:
        db.close()
    # RAG 인덱스가 없으면 1회 빌드 (있으면 그대로 사용 — 인덱싱/서비스 분리)
    from app.core.config import get_settings

    # RAG 인덱스가 없거나 임베딩 모델이 바뀌었으면 재빌드 (stale 인덱스 방지)
    from app.rag.build_index import build_index, index_is_current

    if not index_is_current():
        build_index()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="승승장구몰 AI 커머스 에이전트",
        version="0.2.0",
        lifespan=lifespan,
    )
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
