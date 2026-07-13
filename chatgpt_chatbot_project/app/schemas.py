# app/schemas.py
# ------------------------------------------------------------
# 이 파일은 FastAPI 요청(Request)과 응답(Response)의 데이터 형식을 정의합니다.
# Pydantic 모델을 사용하면 잘못된 데이터가 들어왔을 때 FastAPI가 자동으로 검증합니다.
# ------------------------------------------------------------

# typing 모듈에서 List와 Optional 타입을 가져옵니다.
# List는 여러 개의 데이터를 담는 리스트 자료형의 내부 타입을 명확히 표현할 때 사용합니다.
# Optional은 값이 있을 수도 있고 없을 수도(None) 있는 필드를 표현할 때 사용합니다.
from typing import List, Literal, Optional

# pydantic의 BaseModel과 Field를 가져옵니다.
# BaseModel은 데이터 검증 모델의 기본 클래스입니다.
# Field는 각 필드의 설명, 기본값, 길이/범위 제한 등을 지정할 때 사용합니다.
from pydantic import BaseModel, Field


# 채팅 메시지 1개의 구조를 정의하는 클래스입니다.
# 사용자의 메시지와 챗봇의 메시지를 같은 형식으로 다루기 위해 사용합니다.
class ChatMessage(BaseModel):
    # role은 메시지를 보낸 주체를 의미합니다.
    # OpenAI Chat Completions API에서는 일반적으로 system, user, assistant 역할을 사용합니다.
    role: str = Field(
        ...,                                      # ...은 필수 입력값이라는 뜻입니다.
        description="메시지 역할: system, user, assistant 중 하나",
        examples=["user"],
    )

    # content는 실제 메시지 내용입니다.
    # min_length=1을 지정하여 빈 문자열이 들어오지 않도록 검증합니다.
    content: str = Field(
        ...,
        min_length=1,
        description="메시지 본문",
        examples=["FastAPI가 무엇인가요?"],
    )


# 사용자가 설정 메뉴에서 조정할 수 있는 생성 옵션들을 담는 클래스입니다.
# 모든 값은 선택 사항(Optional)이며, 값이 없으면 서버 기본값을 사용합니다.
class ChatSettings(BaseModel):
    # system_instruction은 챗봇의 역할과 답변 스타일을 지정하는 지시문입니다.
    # 값이 없으면 서비스 계층의 기본 지시문을 사용합니다.
    system_instruction: Optional[str] = Field(
        default=None,
        description="System Instruction (챗봇 역할/말투 지정). 없으면 기본값 사용",
        examples=["너는 항상 존댓말로 짧고 명확하게 답변하는 비서다."],
    )

    # model은 사용할 OpenAI 모델명입니다.
    # 값이 없으면 환경 변수 OPENAI_MODEL 또는 기본 모델을 사용합니다.
    model: Optional[str] = Field(
        default=None,
        description="사용할 모델명. 없으면 서버 기본 모델 사용",
        examples=["gpt-4o-mini"],
    )

    # temperature는 답변의 무작위성(창의성) 정도입니다.
    # 0에 가까울수록 일관적이고, 값이 클수록 다양해집니다.
    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="창의성 정도 (0.0 ~ 2.0). gpt-5/o 계열에서는 자동으로 무시됩니다.",
        examples=[0.7],
    )

    # top_p는 확률 상위 토큰만 후보로 사용하는 누적 확률 임계값입니다.
    top_p: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="누적 확률 샘플링 값 (0.0 ~ 1.0). gpt-5/o 계열에서는 자동으로 무시됩니다.",
        examples=[1.0],
    )

    # top_k는 확률 상위 k개의 토큰만 후보로 두는 값입니다.
    # 참고: OpenAI Chat Completions API는 top_k를 직접 지원하지 않아,
    #       값이 있어도 실제 호출에는 반영되지 않을 수 있습니다(UI 실습용으로 포함).
    top_k: Optional[int] = Field(
        default=None,
        ge=0,
        description="상위 k개 토큰 후보 제한. (OpenAI Chat API 미지원, 실습용 필드)",
        examples=[40],
    )

    # max_output_tokens는 생성할 답변의 최대 토큰 수입니다.
    max_output_tokens: Optional[int] = Field(
        default=None,
        ge=1,
        le=32000,
        description="답변 최대 토큰 수",
        examples=[1024],
    )

    # reasoning_effort는 gpt-5 / o 계열 추론 모델이 답변 전에 얼마나 깊게
    # 내부 추론을 할지 정하는 값입니다. 값이 클수록 품질은 오를 수 있지만
    # 추론 토큰 사용량과 응답 시간, 비용이 늘어납니다.
    # minimal < low < medium < high 순서이며, 값이 없으면 모델 기본값(medium)을 사용합니다.
    # 일반 모델(gpt-4o 등)에는 적용되지 않으며, 서비스 계층에서 자동으로 무시됩니다.
    reasoning_effort: Optional[Literal["minimal", "low", "medium", "high"]] = Field(
        default=None,
        description="추론 강도 (minimal/low/medium/high). gpt-5·o 계열에만 적용, 없으면 기본값(medium)",
        examples=["low"],
    )


# 클라이언트가 /api/chat 엔드포인트로 보낼 요청 데이터 구조입니다.
class ChatRequest(BaseModel):
    # message는 사용자가 새로 입력한 질문입니다.
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="사용자가 입력한 새 질문",
        examples=["파이썬 FastAPI의 장점을 알려줘"],
    )

    # history는 이전 대화 내역입니다.
    # 기본값을 빈 리스트로 두어 첫 질문에서도 오류 없이 처리되게 합니다.
    history: List[ChatMessage] = Field(
        default_factory=list,
        description="이전 대화 내역",
    )

    # settings는 설정 메뉴에서 조정한 생성 옵션입니다.
    # 값이 없으면 서버 기본값으로 동작합니다.
    settings: ChatSettings = Field(
        default_factory=ChatSettings,
        description="생성 옵션 (system instruction, model, temperature 등)",
    )


# 서버가 클라이언트에게 돌려줄 응답 데이터 구조입니다.
class ChatResponse(BaseModel):
    # reply는 ChatGPT 또는 데모 응답이 생성한 답변입니다.
    reply: str = Field(
        ...,
        description="챗봇 답변",
        examples=["FastAPI는 파이썬 기반의 빠른 웹 API 프레임워크입니다."],
    )

    # used_demo_mode는 실제 OpenAI API를 호출했는지, 데모 응답을 사용했는지 알려줍니다.
    # API 키가 없으면 True가 됩니다.
    used_demo_mode: bool = Field(
        default=False,
        description="OPENAI_API_KEY가 없어서 데모 응답을 사용했는지 여부",
    )

    # model은 실제로 응답을 생성하는 데 사용된 모델명입니다.
    model: str = Field(
        default="",
        description="실제 사용된 모델명",
        examples=["gpt-4o-mini"],
    )


# /api/config 응답 구조입니다.
# 프론트엔드가 기본 모델명, 선택 가능한 모델 목록 등을 표시할 때 사용합니다.
class ConfigResponse(BaseModel):
    # 서버가 사용하는 기본 모델명입니다.
    default_model: str = Field(..., description="서버 기본 모델명")

    # 설정 화면의 모델 선택 목록에 표시할 추천 모델 목록입니다.
    available_models: List[str] = Field(
        default_factory=list,
        description="설정 화면에 표시할 추천 모델 목록",
    )

    # 기본 System Instruction 문구입니다.
    default_system_instruction: str = Field(
        default="",
        description="서버 기본 System Instruction",
    )

    # API 키가 설정되어 있는지 여부입니다. (데모 모드 판별용)
    has_api_key: bool = Field(
        default=False,
        description="OPENAI_API_KEY 설정 여부",
    )
