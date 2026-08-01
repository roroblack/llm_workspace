"""HuggingFace pipeline 싱글톤 레지스트리.

pipeline() 호출은 (1) 모델 다운로드 (2) 가중치 로딩 (3) 토크나이저 준비를
전부 수행하므로 요청마다 만들면 안 된다. 프로세스당 태스크별 1개만 만들고
재사용한다. 최초 1회는 다운로드 때문에 수십 초~수 분이 걸릴 수 있다.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any

from transformers import pipeline as hf_pipeline

from app.core.config import get_settings

logger = logging.getLogger(__name__)

CLASSIFICATION = "classification"
SUMMARIZATION = "summarization"
TRANSLATION = "translation"

ALL_TASKS: tuple[str, ...] = (CLASSIFICATION, SUMMARIZATION, TRANSLATION)


@dataclass
class LoadedPipeline:
    """로딩된 파이프라인 + 메타데이터."""

    task: str
    model_name: str
    pipe: Any
    load_seconds: float
    extra_call_kwargs: dict[str, Any] = field(default_factory=dict)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """호출 시 모델 고유 kwargs(예: NLLB 언어코드)를 자동으로 합쳐준다."""
        merged = {**self.extra_call_kwargs, **kwargs}
        return self.pipe(*args, **merged)


class PipelineRegistry:
    """태스크별 파이프라인을 lazy 하게 만들고 캐싱한다 (스레드 안전)."""

    def __init__(self) -> None:
        self._cache: dict[str, LoadedPipeline] = {}
        # 태스크별 락: 요약 로딩이 분류 로딩을 막지 않게 한다.
        self._locks: dict[str, threading.Lock] = {
            CLASSIFICATION: threading.Lock(),
            SUMMARIZATION: threading.Lock(),
            TRANSLATION: threading.Lock(),
        }

    # ------------------------------------------------------------------ 공개 API
    def get(self, task: str) -> LoadedPipeline:
        cached = self._cache.get(task)
        if cached is not None:
            return cached

        lock = self._locks.get(task)
        if lock is None:
            raise ValueError(f"알 수 없는 태스크: {task}")

        with lock:
            # 락 대기 중에 다른 스레드가 이미 로딩했을 수 있다 (double-checked locking).
            cached = self._cache.get(task)
            if cached is not None:
                return cached

            loaded = self._build(task)
            self._cache[task] = loaded
            return loaded

    def preload(self, tasks: list[str]) -> None:
        """지정한 태스크만 미리 로딩한다.

        3종을 한꺼번에 올리면 fp32 가중치 합계가 약 3.5GB라, 가용 메모리가
        부족한 환경에서는 OpenBLAS 할당 실패로 프로세스가 죽는다. 그래서
        '전부'가 아니라 '고른 것만' 올릴 수 있게 한다.
        """
        for task in tasks:
            self.get(task)

    def status(self) -> dict[str, dict[str, Any]]:
        """헬스체크용. 아직 로딩 안 된 태스크도 어떤 모델을 쓸지 함께 보고한다."""
        settings = get_settings()
        planned = {
            CLASSIFICATION: settings.classification_model,
            SUMMARIZATION: settings.summarization_model,
            TRANSLATION: settings.translation_model,
        }
        preloaded = set(settings.preload_tasks(ALL_TASKS))
        return {
            task: {
                "model": planned[task],
                "loaded": task in self._cache,
                "preload": task in preloaded,
                "load_seconds": round(self._cache[task].load_seconds, 2)
                if task in self._cache
                else None,
            }
            for task in planned
        }

    # ------------------------------------------------------------------ 내부 구현
    def _build(self, task: str) -> LoadedPipeline:
        settings = get_settings()
        common: dict[str, Any] = {"device": settings.device}
        if settings.cache_dir is not None:
            common["model_kwargs"] = {"cache_dir": str(settings.cache_dir)}

        if task == CLASSIFICATION:
            model_name = settings.classification_model
            hf_task, init_kwargs, call_kwargs = "text-classification", {}, {}

        elif task == SUMMARIZATION:
            model_name = settings.summarization_model
            hf_task, init_kwargs, call_kwargs = "summarization", {}, {}

        elif task == TRANSLATION:
            model_name = settings.translation_model
            hf_task = "translation"
            if "nllb" in model_name.lower():
                # NLLB는 FLORES-200 언어 코드를 토크나이저에 넘겨야 한다.
                init_kwargs = {
                    "src_lang": settings.translation_src_lang,
                    "tgt_lang": settings.translation_tgt_lang,
                }
                call_kwargs = {}
            else:
                # Marian(opus-mt) 등 언어쌍 전용 모델은 코드가 불필요하다.
                init_kwargs, call_kwargs = {}, {}
        else:
            raise ValueError(f"알 수 없는 태스크: {task}")

        logger.info("[HF] %s 파이프라인 로딩 시작: %s", task, model_name)
        started = time.perf_counter()
        pipe = hf_pipeline(hf_task, model=model_name, **common, **init_kwargs)
        elapsed = time.perf_counter() - started
        logger.info("[HF] %s 로딩 완료 (%.2fs): %s", task, elapsed, model_name)

        return LoadedPipeline(
            task=task,
            model_name=model_name,
            pipe=pipe,
            load_seconds=elapsed,
            extra_call_kwargs=call_kwargs,
        )


registry = PipelineRegistry()


# ---------------------------------------------------------------------- 유틸
def chunk_by_tokens(text: str, tokenizer: Any, max_tokens: int) -> list[str]:
    """토크나이저 기준으로 텍스트를 max_tokens 이하 청크로 나눈다.

    요약 모델(BART 계열)은 입력이 1024 토큰으로 잘리므로, 긴 문서는
    잘라 버리지 말고 나눠서 요약한 뒤 합쳐야 뒷부분 내용이 유실되지 않는다.
    문장 경계를 지키기 위해 마침표 기준으로 먼저 쪼갠 뒤 토큰 수로 묶는다.
    """
    sentences = _split_sentences(text)
    if not sentences:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for sentence in sentences:
        n = len(tokenizer.encode(sentence, add_special_tokens=False))

        # 문장 하나가 이미 한계를 넘으면 토큰 단위로 강제 분할한다.
        if n > max_tokens:
            if current:
                chunks.append(" ".join(current))
                current, current_tokens = [], 0
            chunks.extend(_force_split(sentence, tokenizer, max_tokens))
            continue

        if current_tokens + n > max_tokens and current:
            chunks.append(" ".join(current))
            current, current_tokens = [], 0

        current.append(sentence)
        current_tokens += n

    if current:
        chunks.append(" ".join(current))
    return chunks


def _split_sentences(text: str) -> list[str]:
    """의존성 없이 문장 분리. 종결부호 뒤 공백을 경계로 본다."""
    import re

    parts = re.split(r"(?<=[.!?。！？])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _force_split(sentence: str, tokenizer: Any, max_tokens: int) -> list[str]:
    ids = tokenizer.encode(sentence, add_special_tokens=False)
    return [
        tokenizer.decode(ids[i : i + max_tokens], skip_special_tokens=True)
        for i in range(0, len(ids), max_tokens)
    ]
