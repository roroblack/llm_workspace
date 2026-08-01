"""요청/응답 스키마.

Swagger UI 예시(examples)는 프로젝트개요와구조.txt 의 테스트 케이스를 그대로 넣어
문서를 열자마자 바로 실행해 볼 수 있게 한다.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.core.config import get_settings

# 요약 길이 기본값은 설정에서 가져온다.
# 여기에 숫자를 하드코딩하면 .env 의 SUMMARY_DEFAULT_* 가 무시되는 죽은 설정이 된다.
_settings = get_settings()


# --------------------------------------------------------------------- 공통
class ErrorResponse(BaseModel):
    detail: str


# --------------------------------------------------- 1. Text Classification
class ClassifyRequest(BaseModel):
    text: str | None = Field(
        default=None,
        description="분류할 문장 1개. texts 와 둘 중 하나만 사용한다.",
    )
    texts: list[str] | None = Field(
        default=None,
        description="배치 분류용 문장 목록. text 와 둘 중 하나만 사용한다.",
    )
    top_k: int = Field(
        default=1,
        ge=1,
        le=10,
        description="반환할 라벨 개수. 2 이상이면 전체 라벨의 확률 분포를 볼 수 있다.",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "The lecture was clear, well structured, and very helpful "
                    "for understanding AI fundamentals."
                },
                {
                    "text": "I thought this course would be great, but it turned out "
                    "to be a complete waste of time."
                },
                {
                    "texts": [
                        "This service is extremely slow, unreliable, and the support "
                        "team never responds.",
                        "The product works, but it feels outdated and lacks important "
                        "features.",
                    ],
                    "top_k": 2,
                },
            ]
        }
    }

    @model_validator(mode="after")
    def _exactly_one_input(self) -> "ClassifyRequest":
        if (self.text is None) == (self.texts is None):
            raise ValueError("text 또는 texts 중 정확히 하나를 지정해야 합니다.")
        if self.texts is not None and not self.texts:
            raise ValueError("texts 가 비어 있습니다.")
        return self

    def as_list(self) -> list[str]:
        return [self.text] if self.text is not None else list(self.texts or [])


class LabelScore(BaseModel):
    label: str = Field(description="모델이 예측한 라벨 (예: POSITIVE / NEGATIVE)")
    score: float = Field(description="해당 라벨의 확률 (0~1, softmax 결과)")


class ClassifyItem(BaseModel):
    text: str
    predictions: list[LabelScore] = Field(
        description="score 내림차순. top_k=1 이면 최상위 1개만 들어 있다."
    )


class ClassifyResponse(BaseModel):
    model: str
    count: int
    results: list[ClassifyItem]
    elapsed_ms: float


# ---------------------------------------------------------- 2. Summarization
class SummarizeRequest(BaseModel):
    text: str = Field(min_length=1, description="요약할 원문")
    max_length: int = Field(
        default=_settings.summary_default_max_length,
        ge=10,
        le=512,
        description="요약문 최대 토큰 수 (글자 수 아님)",
    )
    min_length: int = Field(
        default=_settings.summary_default_min_length,
        ge=5,
        le=512,
        description="요약문 최소 토큰 수 (글자 수 아님)",
    )
    do_sample: bool = Field(
        default=False,
        description="False면 결정론적(beam search) — 같은 입력에 같은 요약이 나온다.",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "Artificial intelligence has rapidly transformed various "
                    "industries over the past decade. In healthcare, AI is being used "
                    "to assist doctors in diagnosing diseases more accurately and "
                    "efficiently. In finance, machine learning models analyze vast "
                    "amounts of data to detect fraud and optimize investment "
                    "strategies. However, despite these advancements, concerns remain "
                    "regarding data privacy, algorithmic bias, and job displacement. "
                    "Experts emphasize that responsible AI development, combined with "
                    "proper regulation and ethical guidelines, is essential to ensure "
                    "that the benefits of AI outweigh its potential risks.",
                    "max_length": 120,
                    "min_length": 40,
                },
                {
                    "text": "Large language models have become a central topic in "
                    "artificial intelligence research. These models are trained on "
                    "massive datasets and are capable of performing tasks such as "
                    "translation, summarization, and question answering. Despite their "
                    "impressive capabilities, they require significant computational "
                    "resources and raise concerns related to environmental impact. "
                    "Researchers are now focusing on model efficiency, parameter "
                    "reduction, and knowledge distillation techniques to address these "
                    "challenges. As AI systems become more integrated into daily life, "
                    "transparency and explainability are increasingly important.",
                    "max_length": 100,
                    "min_length": 30,
                },
            ]
        }
    }

    @model_validator(mode="after")
    def _length_order(self) -> "SummarizeRequest":
        if self.min_length >= self.max_length:
            raise ValueError("min_length 는 max_length 보다 작아야 합니다.")
        return self


class SummarizeResponse(BaseModel):
    model: str
    summary: str
    chunks: int = Field(
        description="입력을 몇 조각으로 나눠 요약했는지. 1이면 분할 없이 한 번에 처리."
    )
    strategy: Literal["single", "map-reduce"] = Field(
        description="single=단일 요약, map-reduce=청크별 요약 후 재요약"
    )
    input_chars: int
    summary_chars: int
    elapsed_ms: float


# ------------------------------------------------------------- 3. Translation
class TranslateRequest(BaseModel):
    text: str = Field(min_length=1, description="번역할 문장")
    max_length: int = Field(
        default=256, ge=10, le=1024, description="번역 결과 최대 토큰 수"
    )
    src_lang: str | None = Field(
        default=None,
        description="NLLB 소스 언어 코드(FLORES-200). 미지정 시 설정값 사용 (eng_Latn).",
    )
    tgt_lang: str | None = Field(
        default=None,
        description="NLLB 타깃 언어 코드(FLORES-200). 미지정 시 설정값 사용 (kor_Hang).",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"text": "Hello, how are you doing today?"},
                {
                    "text": "Although the project was challenging, the team "
                    "successfully completed it on time."
                },
                {
                    "text": "Large language models require careful fine-tuning and "
                    "evaluation to ensure reliable performance in real-world "
                    "applications."
                },
                {
                    "text": "What are the ethical challenges associated with deploying "
                    "AI systems in healthcare?"
                },
            ]
        }
    }


class TranslateResponse(BaseModel):
    model: str
    source_text: str
    translated_text: str
    src_lang: str | None
    tgt_lang: str | None
    elapsed_ms: float


# ------------------------------------------------------------------ 헬스체크
class PipelineStatus(BaseModel):
    model: str
    loaded: bool = Field(description="현재 메모리에 올라와 있는지")
    preload: bool = Field(
        description="PRELOAD_MODELS 에 지정되어 기동 시 미리 로딩되는 대상인지"
    )
    load_seconds: float | None = Field(description="로딩에 걸린 시간. 미로딩이면 null")


class HealthResponse(BaseModel):
    status: Literal["ok"]
    app: str
    version: str
    device: str
    pipelines: dict[str, PipelineStatus]
