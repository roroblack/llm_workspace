"""NLP 엔드포인트: 감성분석 / 요약 / 번역.

추론은 CPU 바운드 blocking 작업이라 async 함수 안에서 그대로 돌리면
이벤트 루프를 막는다. 전부 def(동기)로 선언해 FastAPI 가 threadpool 로
넘기게 한다.



Text Classification (감성분석) 예시 모델
distilbert 기반의 SST-2 (영어 감성분석)로 가볍고 빠름
  CLS_MODEL: str = "distilbert-base-uncased-finetuned-sst-2-english"

Summarization(요약) 예시 모델: BART CNN 요약 모델
BART 는 seq2seq 모델로 요약/번역 등에 활용됨. bart-large-cnn 은 요약으로 유명함
  SUM_MODEL: str = "facebook/bart-large-cnn"

Translation(번역) 예시 모델: MarianMT (영->한)
언어쌍에 따라 모델명이 달라짐
  TRANS_MODEL: str = "facebook/nllb-200-distilled-600M"

CPU 환경이므로 device = -1 (pipeline 에서 -1은 CPU를 의미함)
  DEVICE: int = -1  # MacOS GPU 제공됨: GPU 0 (CUDA:0) -> 0, GPU 1 -> 1 로 지정함

요약 파라미터 기본값
  SUM_MAX_LENGTH: int = 120
  SUM_MIN_LENGTH: int = 30

class end -----------------
settings = Settings()  # 싱글톤 적용
'''
Hugging Face 파이프라인을 서버 시작시 1번만 로딩하기 위한 모듈임
  => 요청마다 모델을 로딩하면 요청 처리 속도가 매우 느림
  => 서버가 구동될 때 모델을 미리 메모리에 올려두고, 요청시 로딩되어 있는 모델을 사용하게 함
pipeline 은 전처리(토크나이징) -> 모델 추론 -> 후처리를 묶어주는 API 임

API(Application Programming Interface) : 
프로그램과 프로그램이 대화하는 공식 규칙(약속)
=> 프로그램은 API를 통해 다른 프로그램의 기능을 사용함
예>
날씨 앱 --> 기상청 API 호출 : 기상청이 제공하는 날씨 정보 처리하는 프로그램을 연결 사용함
로그인 --> 인증 서버 API 호출
쇼핑몰 --> 결제 API 호출
AI 서비스 --> OpenAI API 호출

API 동작 구조:
클라이언트 -> 요청 (Request) -> 서버 API (요청을 처리하고 결과 반환) -> 응답(Response) -> 클라이언트

'''

'''
NLP API 라우터
 
/nlp/classify : 텍스트 분류
/nlp/summarize : 요약
/nlp/translate : 번역

NLP (Natural Language Processing : 자연어 처리):
사람이 사용하는 언어(자연어)를 컴퓨터가 이해하고 분석하고 생성하도록 만드는 AI 기술 분야임
NLP API : 
자연어 처리 기능을 API 형태로 제공하는 서비스임
텍스트를 주면 -> 분석/이해/결과를 돌려주는 API
처리하는 대표 기능:
형태소 분석 / 토큰화"강아지는 귀엽다"-> ["강아지", "는", "귀엽다"]
감성 분석 (Sentiment Analysis)
입력: "이 영화 정말 재미있다"
출력: {"sentiment": "POSITIVE"}
문장 분류 / 의도 분석"환불하고 싶어요"-> intent: "refund_request"
개체명 인식 (NER)"홍길동은 서울에 산다"-> [홍길동: PERSON, 서울: LOCATION]
요약 (Summarization)
긴 뉴스 기사 -> 핵심 문장 3줄
질의 응답 (Question Answering)
질문 : "대한민국 수도는?"
답 : "서울"
문장 생성 / 번역
한국어 -> 영어
질문 -> 답변 생성
'''

"""

from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.core.hf import pipelines as hf
from app.models.schemas import (
    ClassifyItem,
    ClassifyRequest,
    ClassifyResponse,
    ErrorResponse,
    LabelScore,
    SummarizeRequest,
    SummarizeResponse,
    TranslateRequest,
    TranslateResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/nlp",
    tags=["NLP"],
    responses={
        422: {"model": ErrorResponse, "description": "입력 검증 실패"},
        503: {"model": ErrorResponse, "description": "모델 로딩/추론 실패"},
    },
)


def _guard_length(*texts: str) -> None:
    limit = get_settings().max_input_chars
    for t in texts:
        if len(t) > limit:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"입력이 너무 깁니다 ({len(t)}자). 최대 {limit}자까지 허용됩니다.",
            )


def _load(task: str) -> hf.LoadedPipeline:
    try:
        return hf.registry.get(task)
    except Exception as exc:  # 다운로드 실패/디스크 부족/네트워크 차단 등
        logger.exception("[HF] %s 파이프라인 로딩 실패", task)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{task} 모델을 로딩할 수 없습니다: {exc}",
        ) from exc


# ----------------------------------------------------------- 1. 감성분석
@router.post(
    "/classify",
    response_model=ClassifyResponse,
    summary="텍스트 분류(감성분석)",
    description=(
        "문장 1개(`text`) 또는 여러 개(`texts`)를 감성 분류한다.\n\n"
        "- `label`: 모델이 학습한 라벨명 (SST-2 모델은 POSITIVE / NEGATIVE 2진 분류)\n"
        "- `score`: softmax 확률. 0.9 이상이면 확신, 0.5~0.7 이면 경계 케이스로 읽는다.\n"
        "- 중립 라벨이 없는 모델이므로 중립 문장도 둘 중 하나로 강제 분류된다. "
        "`top_k=2` 로 두 라벨 확률을 함께 보면 경계 여부를 판단하기 쉽다."
    ),
)
def classify(req: ClassifyRequest) -> ClassifyResponse:
    texts = req.as_list()
    settings = get_settings()

    if len(texts) > settings.max_batch_size:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"배치는 한 번에 최대 {settings.max_batch_size}건까지 가능합니다.",
        )
    _guard_length(*texts)

    loaded = _load(hf.CLASSIFICATION)
    started = time.perf_counter()
    try:
        raw = loaded(texts, top_k=req.top_k)
    except Exception as exc:
        logger.exception("[HF] 분류 추론 실패")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"분류 추론 중 오류: {exc}",
        ) from exc
    elapsed = (time.perf_counter() - started) * 1000

    results = [
        ClassifyItem(
            text=text,
            predictions=[
                LabelScore(label=p["label"], score=float(p["score"]))
                for p in _as_pred_list(item)
            ],
        )
        for text, item in zip(texts, _normalize_batch(raw, len(texts)))
    ]

    return ClassifyResponse(
        model=loaded.model_name,
        count=len(results),
        results=results,
        elapsed_ms=round(elapsed, 1),
    )


def _normalize_batch(raw: Any, n: int) -> list[Any]:
    """top_k 지정 여부/입력 개수에 따라 출력 중첩이 달라지는 것을 흡수한다."""
    if isinstance(raw, list) and len(raw) == n and n != 1:
        return raw
    if isinstance(raw, list) and n == 1:
        # [[{...}]] 또는 [{...}] 두 형태 모두 가능
        if raw and isinstance(raw[0], list):
            return raw
        return [raw]
    return raw if isinstance(raw, list) else [raw]


def _as_pred_list(item: Any) -> list[dict]:
    if isinstance(item, dict):
        return [item]
    return list(item)


# -------------------------------------------------------------- 2. 요약
@router.post(
    "/summarize",
    response_model=SummarizeResponse,
    summary="추상적 요약",
    description=(
        "긴 문서를 요약한다.\n\n"
        "- BART 계열 요약 모델은 입력 상한(약 1024 토큰)이 있어 그냥 넣으면 "
        "뒷부분이 **잘려서 무시**된다.\n"
        "- 이 엔드포인트는 입력이 상한을 넘으면 문장 경계 기준으로 청크를 나눠 "
        "각각 요약하고(map), 그 요약들을 다시 요약한다(reduce).\n"
        "- `strategy` 필드로 어떤 경로를 탔는지, `chunks` 로 몇 조각이었는지 확인할 수 있다.\n"
        "- `max_length`/`min_length` 는 **글자 수가 아니라 토큰 수**다."
    ),
)
def summarize(req: SummarizeRequest) -> SummarizeResponse:
    _guard_length(req.text)
    settings = get_settings()
    loaded = _load(hf.SUMMARIZATION)

    started = time.perf_counter()
    tokenizer = loaded.pipe.tokenizer
    chunk_limit = min(settings.summary_chunk_tokens, _model_input_limit(tokenizer))

    n_input_tokens = len(tokenizer.encode(req.text, add_special_tokens=False))
    try:
        if n_input_tokens <= chunk_limit:
            summary = _run_summary(loaded, req.text, req.max_length, req.min_length,
                                   req.do_sample)
            chunks, strategy = 1, "single"
        else:
            pieces = hf.chunk_by_tokens(req.text, tokenizer, chunk_limit)
            chunks, strategy = len(pieces), "map-reduce"

            # map: 청크별 요약. 최종 길이를 넘지 않게 청크당 예산을 나눈다.
            per_chunk_max = max(30, req.max_length // max(1, len(pieces)) + 20)
            per_chunk_min = max(10, min(req.min_length // max(1, len(pieces)),
                                        per_chunk_max - 5))
            partials = [
                _run_summary(loaded, piece, per_chunk_max, per_chunk_min, req.do_sample)
                for piece in pieces
            ]

            # reduce: 부분 요약을 이어 붙여 한 번 더 요약한다.
            merged = " ".join(partials)
            if len(tokenizer.encode(merged, add_special_tokens=False)) > req.min_length:
                summary = _run_summary(loaded, merged, req.max_length, req.min_length,
                                       req.do_sample)
            else:
                summary = merged
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("[HF] 요약 추론 실패")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"요약 추론 중 오류: {exc}",
        ) from exc

    elapsed = (time.perf_counter() - started) * 1000
    return SummarizeResponse(
        model=loaded.model_name,
        summary=summary,
        chunks=chunks,
        strategy=strategy,
        input_chars=len(req.text),
        summary_chars=len(summary),
        elapsed_ms=round(elapsed, 1),
    )


def _run_summary(
    loaded: hf.LoadedPipeline,
    text: str,
    max_length: int,
    min_length: int,
    do_sample: bool,
) -> str:
    out = loaded(
        text,
        max_length=max_length,
        min_length=min_length,
        do_sample=do_sample,
        truncation=True,
    )
    return out[0]["summary_text"].strip()


def _model_input_limit(tokenizer: Any) -> int:
    """토크나이저가 보고하는 입력 상한. 비정상적으로 크면(무제한 표기) 기본값 사용."""
    limit = getattr(tokenizer, "model_max_length", 1024)
    if not isinstance(limit, int) or limit > 100_000:
        return 1024
    # 특수 토큰/여유분 확보
    return max(128, limit - 24)


# -------------------------------------------------------------- 3. 번역
@router.post(
    "/translate",
    response_model=TranslateResponse,
    summary="번역 (기본 영어 → 한국어)",
    description=(
        "NLLB-200 기반 번역. 기본 언어쌍은 `eng_Latn` → `kor_Hang` 이며 "
        "요청마다 `src_lang`/`tgt_lang` 으로 바꿀 수 있다 (FLORES-200 코드).\n\n"
        "예: `kor_Hang`(한국어), `eng_Latn`(영어), `jpn_Jpan`(일본어), "
        "`zho_Hans`(중국어 간체), `fra_Latn`(프랑스어)\n\n"
        "Marian(`Helsinki-NLP/opus-mt-*`) 계열 모델로 바꾸면 모델 자체가 언어쌍을 "
        "고정하므로 이 두 필드는 무시된다."
    ),
)
def translate(req: TranslateRequest) -> TranslateResponse:
    _guard_length(req.text)
    settings = get_settings()
    loaded = _load(hf.TRANSLATION)

    is_nllb = "nllb" in loaded.model_name.lower()
    src = req.src_lang or (settings.translation_src_lang if is_nllb else None)
    tgt = req.tgt_lang or (settings.translation_tgt_lang if is_nllb else None)

    call_kwargs: dict[str, Any] = {"max_length": req.max_length}
    if is_nllb:
        call_kwargs["src_lang"] = src
        call_kwargs["tgt_lang"] = tgt

    started = time.perf_counter()
    try:
        out = loaded(req.text, **call_kwargs)
    except Exception as exc:
        logger.exception("[HF] 번역 추론 실패")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"번역 추론 중 오류: {exc}",
        ) from exc
    elapsed = (time.perf_counter() - started) * 1000

    return TranslateResponse(
        model=loaded.model_name,
        source_text=req.text,
        translated_text=out[0]["translation_text"].strip(),
        src_lang=src,
        tgt_lang=tgt,
        elapsed_ms=round(elapsed, 1),
    )
