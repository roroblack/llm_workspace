# path: app/models/schemas.py
# 요청/응답 데이터 모델 정의

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class TextIn(BaseModel):
  # 입력 텍스트
  text: str = Field(..., description='입력 텍스트')
# class end ---------------------------


class ClassificationOut(BaseModel):
  # 예: label='POSITIVE', score=0.999999...
  label: str
  score: float
# class end ---------------------------


class SummarizeIn(BaseModel):
  # 요약할 원문
  text: str = Field(..., description="요약할 원문")
  # 기본 파라미터 값 지정 (미지정시 서버 기본값 사용함)
  max_length: Optional[int] = Field(None, description="생성 요약 최대 길이")
  min_length: Optional[int] = Field(None, description="생성 요약 최소 길이")
# class end ---------------------------


class SummarizeOut(BaseModel):
  # 생성 요약 결과
  summary: str
# class end ---------------------------


class TranslateIn(BaseModel):
  text: str = Field(..., description="번역할 텍스트")
# class end ---------------------------


class TranslateOut(BaseModel):
  translation: str
# class end ---------------------------


class HealthOut(BaseModel):
  status: str
  loaded_models: Dict[str, Any]
# class end ---------------------------
        