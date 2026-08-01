# -*- coding: utf-8 -*-
"""FastAPI HTTP 엔드포인트를 정의합니다."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.repositories.consultation_repository import ConsultationRepository
from app.schemas.chat import ChatRequest, ChatResponse, ConsultationResponse
from app.services.ingest_service import ingest_csv_data
from app.services.supervisor_service import SupervisorService
from app.vectordb.chroma_store import ChromaStore

router = APIRouter(prefix="/api")

@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "multi-agent-mcp-rag"}

@router.post("/vector/ingest")
def vector_ingest() -> dict:
    return {"indexed": ingest_csv_data()}

@router.get("/vector/search")
def vector_search(q: str = Query(min_length=1), source: str | None = None, limit: int = 3) -> dict:
    return {"results": ChromaStore().search(q, source=source, limit=limit)}

@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)) -> dict:
    return SupervisorService().process(db, request.question, request.router_type, request.provider)

@router.get("/consultations", response_model=list[ConsultationResponse])
def consultations(limit: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_db)):
    return ConsultationRepository().list_recent(db, limit)
