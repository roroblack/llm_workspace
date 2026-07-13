# 요청과 응답 데이터 구조를 정의하기 위해 Pydantic BaseModel을 가져옵니다.
from pydantic import BaseModel, Field


# LLM 호출 요청에서 공통으로 사용할 입력 데이터 구조입니다.
class LLMRequest(BaseModel):
    # LLM에게 전달할 사용자 입력 문장입니다.
    prompt: str = Field(..., description="LLM에 전달할 사용자 입력 문장")

    # 모델의 역할과 응답 방식을 지정하는 시스템 지시문입니다.
    system_instruction: str = Field("친절하고 정확한 AI 강사처럼 답변하시오.", description="시스템 지시문")

    # 기능 유형입니다. sentence, qa, summary, translation, chat, usecase 중 하나로 사용합니다.
    task_type: str = Field("sentence", description="실행할 LLM 기능 유형")

    # 사용할 모델명을 요청마다 덮어쓸 수 있습니다. 비워두면 .env 기본 모델을 사용합니다.
    model: str | None = Field(None, description="요청별 모델명")

    # 생성 다양성 설정입니다. 낮으면 안정적이고 높으면 창의적입니다.
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="출력 다양성")

    # 확률 누적 범위를 제한하는 설정입니다.
    top_p: float = Field(0.95, ge=0.0, le=1.0, description="Top-p 샘플링")

    # 최대 출력 토큰 수입니다.
    max_output_tokens: int = Field(800, ge=1, le=8192, description="최대 출력 토큰 수")


# LLM 호출 결과를 클라이언트에 반환하기 위한 응답 데이터 구조입니다.
class LLMResponse(BaseModel):
    # 어떤 공급자 API를 사용했는지 표시합니다.
    provider: str

    # 실제 호출에 사용된 모델명을 표시합니다.
    model: str

    # 실행한 기능 유형을 표시합니다.
    task_type: str

    # LLM이 생성한 최종 텍스트입니다.
    result: str
