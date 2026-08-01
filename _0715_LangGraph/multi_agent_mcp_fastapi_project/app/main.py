# -*- coding: utf-8 -*-
"""FastAPI 애플리케이션 진입점입니다."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
from app.api.routes import router
from app.core.config import PROJECT_ROOT, get_settings
from app.db.database import create_tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield

settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
app.include_router(router)

@app.get("/", include_in_schema=False)
def index():
    return FileResponse(PROJECT_ROOT / "app" / "static" / "index.html")
