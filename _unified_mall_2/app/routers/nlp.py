"""NLP/ML 라우터: 의도분류 / 감성분석 / 상품추천."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.ml.intent import classify_intent
from app.ml.recommend import recommend_products
from app.ml.sentiment import analyze_sentiment

router = APIRouter(prefix="/api/nlp", tags=["nlp"])


class TextRequest(BaseModel):
    text: str = Field(min_length=1)


class RecommendRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)


@router.post("/intent")
def intent(body: TextRequest) -> dict:
    return classify_intent(body.text)


@router.post("/sentiment")
def sentiment(body: TextRequest) -> dict:
    return analyze_sentiment(body.text)


@router.post("/recommend")
def recommend(body: RecommendRequest, db: Session = Depends(get_db)) -> dict:
    return recommend_products(db, body.query, body.top_k)
