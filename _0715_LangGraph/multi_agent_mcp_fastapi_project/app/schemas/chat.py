# -*- coding: utf-8 -*-
"""FastAPI 요청과 응답에 사용하는 Pydantic 스키마입니다."""
from datetime import datetime
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000, description="고객 질문")
    router_type: str = Field(default="hybrid", pattern="^(rule|llm|hybrid)$")
    provider: str | None = Field(default=None, pattern="^(gemini|openai)$")

class ChatResponse(BaseModel):
    consultation_id: int
    route: str
    answer: str
    evidence: list[str]
    provider: str

class ConsultationResponse(BaseModel):
    id: int
    question: str
    route: str
    provider: str
    answer: str
    evidence: str
    created_at: datetime
    model_config = {"from_attributes": True}
