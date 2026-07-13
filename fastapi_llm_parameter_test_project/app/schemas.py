# -*- coding: utf-8 -*-
"""FastAPI 요청/응답 데이터 구조를 정의하는 파일입니다."""

# 타입 힌트를 위해 Optional, List, Literal을 불러옵니다.
from typing import Optional, List, Literal

# 요청 데이터 검증을 위해 Pydantic의 BaseModel과 Field를 불러옵니다.
from pydantic import BaseModel, Field


# 어떤 LLM 공급자를 호출할지 나타내는 타입입니다. (gemini 또는 openai)
Provider = Literal["gemini", "openai"]


class BasicPromptRequest(BaseModel):
    """기본 LLM 호출 요청 데이터입니다."""

    # 호출할 LLM 공급자를 선택합니다. (gemini 또는 openai)
    provider: Provider = Field(default="gemini", description="호출할 LLM 공급자")

    # 사용자가 LLM에게 보낼 질문 또는 지시문입니다.
    prompt: str = Field(default="승승장구몰을 한 문장으로 홍보해줘.", description="LLM에게 보낼 입력 문장")

    # LLM 답변의 무작위성을 조절하는 값입니다.
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="생성 무작위성")

    # 답변 최대 토큰 수를 제한합니다.
    max_output_tokens: Optional[int] = Field(default=300, ge=1, le=4096, description="최대 출력 토큰 수")


class RoleChatRequest(BaseModel):
    """시스템 지시를 포함한 LLM 호출 요청 데이터입니다."""

    # 호출할 LLM 공급자를 선택합니다. (gemini 또는 openai)
    provider: Provider = Field(default="gemini", description="호출할 LLM 공급자")

    # 모델에게 부여할 역할 또는 규칙입니다.
    system_instruction: str = Field(default="너는 승승장구몰의 친절한 CS 상담원이다. 존댓말로 간결히 답하라.")

    # 사용자가 입력하는 실제 질문입니다.
    user_message: str = Field(default="환불 얼마나 걸려요?")

    # 생성 무작위성 설정값입니다.
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)

    # 답변 최대 토큰 수입니다.
    max_output_tokens: Optional[int] = Field(default=300, ge=1, le=4096)


class DiversityRequest(BaseModel):
    """temperature 다양성 측정 요청 데이터입니다."""

    # 호출할 LLM 공급자를 선택합니다. (gemini 또는 openai)
    provider: Provider = Field(default="gemini", description="호출할 LLM 공급자")

    # 같은 질문을 여러 번 던질 때 사용할 질문입니다.
    prompt: str = Field(default="승승장구몰을 한 문장으로 홍보해줘.")

    # 다양성을 확인할 temperature 값입니다.
    temperature: float = Field(default=1.0, ge=0.0, le=2.0)

    # 같은 질문을 몇 번 호출할지 지정합니다.
    repeat_count: int = Field(default=5, ge=1, le=10)


class TokenCompareRequest(BaseModel):
    """한국어/영어 토큰 비교 요청 데이터입니다."""

    # 호출할 LLM 공급자를 선택합니다. (gemini 또는 openai)
    provider: Provider = Field(default="gemini", description="호출할 LLM 공급자")

    # 한국어 입력 문장입니다.
    korean_text: str = Field(default="승승장구몰의 무선 블루투스 이어버드를 한 문장으로 친절하게 홍보해줘.")

    # 영어 입력 문장입니다.
    english_text: str = Field(default="Write one friendly sentence promoting SeungSeung Mall's wireless earbuds.")


class LLMResponse(BaseModel):
    """LLM 호출 결과 응답 데이터입니다."""

    # 모델이 생성한 답변입니다.
    text: str

    # 입력 토큰 수입니다.
    prompt_token_count: Optional[int] = None

    # 출력 토큰 수입니다.
    candidates_token_count: Optional[int] = None

    # 전체 토큰 수입니다.
    total_token_count: Optional[int] = None


class DiversityResponse(BaseModel):
    """temperature 다양성 측정 결과 응답 데이터입니다."""

    # 사용한 temperature 값입니다.
    temperature: float

    # 전체 호출 횟수입니다.
    repeat_count: int

    # 생성된 답변 목록입니다.
    answers: List[str]

    # 중복 제거 후 고유 답변 개수입니다.
    unique_count: int
