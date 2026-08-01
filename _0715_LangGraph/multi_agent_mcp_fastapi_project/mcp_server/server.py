# -*- coding: utf-8 -*-
"""Vector 검색과 상담 이력 조회 기능을 MCP Tool로 공개하는 서버입니다."""
import json
from mcp.server.fastmcp import FastMCP
from app.db.database import SessionLocal
from app.repositories.consultation_repository import ConsultationRepository
from app.services.ingest_service import ingest_csv_data
from app.vectordb.chroma_store import ChromaStore

mcp = FastMCP("multi-agent-mall-tools")

@mcp.tool()
def ingest_knowledge() -> str:
    """상품과 FAQ CSV를 ChromaDB에 색인합니다."""
    return json.dumps(ingest_csv_data(), ensure_ascii=False)

@mcp.tool()
def search_products(query: str, limit: int = 3) -> str:
    """상품 지식 컬렉션에서 질문과 의미가 가까운 상품을 검색합니다."""
    return json.dumps(ChromaStore().search(query, source="products", limit=limit), ensure_ascii=False)

@mcp.tool()
def search_faq(query: str, limit: int = 3) -> str:
    """FAQ 지식 컬렉션에서 질문과 의미가 가까운 정책 문서를 검색합니다."""
    return json.dumps(ChromaStore().search(query, source="faq", limit=limit), ensure_ascii=False)

@mcp.tool()
def recent_consultations(limit: int = 10) -> str:
    """MySQL에서 최근 상담 이력을 조회합니다."""
    with SessionLocal() as db:
        rows = ConsultationRepository().list_recent(db, limit)
        data = [{"id": r.id, "question": r.question, "route": r.route, "answer": r.answer} for r in rows]
    return json.dumps(data, ensure_ascii=False)

if __name__ == "__main__":
    mcp.run(transport="stdio")
