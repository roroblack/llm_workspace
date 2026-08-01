"""애플리케이션 설정.

모델 이름/캐시 경로 등 운영 중 바뀔 수 있는 값은 전부 환경변수로 뺀다.
(.env 또는 셸 환경변수로 덮어쓸 수 있음)
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=(),  # model_* 필드명 허용
    )

    # --- 앱 메타 ---
    app_name: str = "HuggingFace NLP Service"
    app_version: str = "1.0.0"

    # --- 모델 (CPU 환경 고려해 경량 모델 기본값) ---
    classification_model: str = "distilbert-base-uncased-finetuned-sst-2-english"
    summarization_model: str = "sshleifer/distilbart-cnn-6-6"
    translation_model: str = "facebook/nllb-200-distilled-600M"

    # NLLB 계열은 언어 코드(FLORES-200)를 명시해야 한다.
    # Marian(opus-mt) 계열을 쓰면 이 값들은 무시된다.
    translation_src_lang: str = "eng_Latn"
    translation_tgt_lang: str = "kor_Hang"

    # --- 실행 환경 ---
    # -1 = CPU, 0 이상 = 해당 GPU index
    device: int = -1
    # HF 캐시 폴더. 미지정 시 ~/.cache/huggingface 사용
    hf_home: str | None = None

    # 서버 기동 시 미리 로딩할 태스크 목록 (쉼표 구분).
    #   ""     → 전부 lazy (첫 요청 때 로딩)
    #   "all"  → 3종 전부. 단, fp32 가중치 합계가 약 3.5GB라 가용 메모리가
    #            부족하면 OpenBLAS 할당 실패로 기동이 죽는다.
    #   "classification,summarization" → 지정한 것만 미리 로딩
    # 자주 쓰는 태스크만 골라 올리면 첫 요청 지연을 없애면서 메모리도 아낄 수 있다.
    preload_models: str = ""

    # --- 추론 기본값/한계 ---
    max_input_chars: int = 20_000  # 요청당 입력 길이 상한 (DoS 방지)
    max_batch_size: int = 32  # 배치 분류 최대 개수
    summary_default_max_length: int = 120
    summary_default_min_length: int = 30
    # 긴 문서 분할 시 청크 하나의 토큰 수 (모델 입력 한계보다 여유 있게)
    summary_chunk_tokens: int = 700

    @property
    def cache_dir(self) -> Path | None:
        return Path(self.hf_home).expanduser() if self.hf_home else None

    def preload_tasks(self, known: tuple[str, ...]) -> list[str]:
        """preload_models 설정을 실제 태스크 목록으로 해석한다.

        오타로 조용히 프리로드가 빠지는 일이 없도록, 모르는 이름은 예외로 알린다.
        """
        raw = self.preload_models.strip().lower()
        if not raw or raw in {"false", "none", "0"}:
            return []
        if raw in {"all", "true", "1"}:
            return list(known)

        wanted = [t.strip() for t in raw.split(",") if t.strip()]
        unknown = [t for t in wanted if t not in known]
        if unknown:
            raise ValueError(
                f"PRELOAD_MODELS 에 알 수 없는 태스크: {unknown}. "
                f"사용 가능: {list(known)} (또는 all / 빈 값)"
            )
        # 중복 제거하되 입력 순서는 유지한다.
        return list(dict.fromkeys(wanted))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """설정 싱글톤. 프로세스당 1회만 파싱한다."""
    return Settings()
