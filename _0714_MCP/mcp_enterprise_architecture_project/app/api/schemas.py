"""FastAPI 요청 검증 모델을 정의합니다."""

# 임의 JSON 객체 타입을 위해 Any를 가져옵니다.
from typing import Any

# Pydantic 모델과 필드 검증을 가져옵니다.
from pydantic import BaseModel, Field


# Assistant 질문 요청 모델입니다.
class AssistantRequest(BaseModel):
    """사용자가 입력한 자연어 요청입니다."""

    # 비어 있지 않은 요청 문자열을 정의합니다.
    message: str = Field(min_length=1, max_length=5000)


# MCP Tool 직접 호출 요청 모델입니다.
class ToolCallRequest(BaseModel):
    """Tool 이름과 JSON 인수를 전달합니다."""

    # 호출할 Tool 이름을 정의합니다.
    name: str = Field(min_length=1)

    # Tool에 전달할 인수를 정의합니다.
    arguments: dict[str, Any] = Field(default_factory=dict)
