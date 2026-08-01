# -*- coding: utf-8 -*-
"""FastAPI 요청과 응답 데이터의 Pydantic 스키마입니다."""

# 요청 필드 검증을 위해 BaseModel과 Field를 가져옵니다.
from pydantic import BaseModel, Field
# 허용된 공급자 문자열을 제한하기 위해 Literal을 가져옵니다.
from typing import Literal


class ChatRequest(BaseModel):
    """통합 비즈니스 에이전트 채팅 요청입니다."""
    message: str = Field(min_length=1, description="분석하거나 실행할 사용자 질문")
    provider: Literal["openai", "gemini"] = Field(default="openai", description="사용할 LLM 공급자")
    thread_id: str = Field(default="business-session", min_length=1, description="멀티턴 대화 구분 값")


class ToolCallRequest(BaseModel):
    """MCP 호환 도구 직접 호출 요청입니다."""
    tool_name: Literal["monthly_sales", "csv_preview", "data_summary", "data_files"]
    month: str = ""
    filename: str = "monthly_sales.csv"
    limit: int = Field(default=10, ge=1, le=100)


class A2AMessageRequest(BaseModel):
    """A2A 전문 에이전트 직접 위임 요청입니다."""
    agent_name: str = Field(min_length=1)
    message: str = Field(min_length=1)
    provider: Literal["openai", "gemini"] = "openai"


class PromptLabRequest(BaseModel):
    """Prompt Engineering 실습용 직접 LLM 호출 요청입니다."""
    # 실험할 사용자 질문(같은 질문을 프롬프트만 바꿔 비교합니다).
    message: str = Field(min_length=1, description="프롬프트 실험에 사용할 사용자 질문")
    # 사용할 LLM 공급자입니다.
    provider: Literal["openai", "gemini"] = Field(default="openai", description="사용할 LLM 공급자")
    # 프리셋 종류(비교/기록용 라벨이며 실제 동작은 아래 프롬프트로 결정됩니다).
    prompt_type: Literal["basic", "expert", "friendly", "step_by_step", "json"] = Field(default="basic", description="선택된 프롬프트 유형 라벨")
    # 화면에서 편집 가능한 System Prompt 전문입니다.
    system_prompt: str = Field(default="", description="모델 역할·규칙을 정의하는 System Prompt")
    # 질문에 덧붙일 수행 지시문입니다.
    instruction: str = Field(default="", description="질문에 함께 전달할 수행 지시문")
    # 생성 다양성을 조절하는 temperature 값입니다.
    temperature: float = Field(default=0.2, ge=0.0, le=2.0, description="샘플링 temperature")
    # 누적 확률 상위 표본만 사용하는 top_p 값입니다.
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="누적 확률 top_p")
    # few-shot 예시 포함 여부입니다.
    few_shot: bool = Field(default=False, description="few-shot 예시 포함 여부")
