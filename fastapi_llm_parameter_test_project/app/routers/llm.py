# -*- coding: utf-8 -*-
"""LLM 실습 테스트용 API 라우터입니다."""

# FastAPI 라우터와 HTTP 오류 처리를 위해 필요한 클래스를 불러옵니다.
from fastapi import APIRouter, HTTPException

# 요청/응답 스키마를 불러옵니다.
from app.schemas import (
    BasicPromptRequest,
    DiversityRequest,
    DiversityResponse,
    LLMResponse,
    RoleChatRequest,
    TokenCompareRequest,
)

# 실제 LLM 호출 로직이 들어 있는 서비스 함수를 불러옵니다.
from app.services.llm_service import (
    gemini_basic_call,
    gemini_role_chat,
    gemini_temperature_diversity,
    gemini_token_compare,
    openai_basic_call,
    openai_role_chat,
    openai_temperature_diversity,
    openai_token_compare,
)

# /api/llm 경로 아래에 API를 묶기 위한 라우터를 생성합니다.
router = APIRouter(prefix="/api/llm", tags=["LLM 실습 테스트"])


# provider 값(gemini/openai)에 따라 어떤 함수를 부를지 정리한 표입니다.
# 각 기능마다 Gemini용/OpenAI용 함수를 나란히 등록해 둡니다.
BASIC_CALLERS = {"gemini": gemini_basic_call, "openai": openai_basic_call}
ROLE_CALLERS = {"gemini": gemini_role_chat, "openai": openai_role_chat}
DIVERSITY_CALLERS = {"gemini": gemini_temperature_diversity, "openai": openai_temperature_diversity}
TOKEN_COMPARE_CALLERS = {"gemini": gemini_token_compare, "openai": openai_token_compare}


@router.post("/basic", response_model=LLMResponse)
def call_basic(request: BasicPromptRequest):
    """선택한 공급자로 기본 호출을 테스트합니다."""

    try:
        # provider 값에 맞는 함수를 골라 호출합니다.
        caller = BASIC_CALLERS[request.provider]
        return caller(
            prompt=request.prompt,
            temperature=request.temperature,
            max_output_tokens=request.max_output_tokens,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/role", response_model=LLMResponse)
def call_role(request: RoleChatRequest):
    """선택한 공급자로 시스템 지시(역할/말투) 호출을 테스트합니다."""

    try:
        # provider 값에 맞는 함수를 골라 호출합니다.
        caller = ROLE_CALLERS[request.provider]
        return caller(
            system_instruction=request.system_instruction,
            user_message=request.user_message,
            temperature=request.temperature,
            max_output_tokens=request.max_output_tokens,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/diversity", response_model=DiversityResponse)
def check_temperature_diversity(request: DiversityRequest):
    """선택한 공급자로 temperature 값에 따른 답변 다양성을 측정합니다."""

    try:
        # provider 값에 맞는 함수를 골라 호출합니다.
        caller = DIVERSITY_CALLERS[request.provider]
        return caller(
            prompt=request.prompt,
            temperature=request.temperature,
            repeat_count=request.repeat_count,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/token-compare")
def compare_korean_english_tokens(request: TokenCompareRequest):
    """선택한 공급자로 한국어와 영어 입력의 토큰 사용량을 비교합니다."""

    try:
        # provider 값에 맞는 함수를 골라 호출합니다.
        caller = TOKEN_COMPARE_CALLERS[request.provider]
        return caller(
            korean_text=request.korean_text,
            english_text=request.english_text,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
