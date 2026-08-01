"""NLLB 캐시가 재다운로드 없이 쓸 수 있는 상태인지 진단한다.

디스크가 빠듯할 때 2.4GB 를 또 받지 않도록, 먼저 '무엇이 없는지'만 확인하고
작은 파일(토크나이저)만 내려받아 본다.
"""

from __future__ import annotations

import sys

from huggingface_hub import hf_hub_download

REPO = "facebook/nllb-200-distilled-600M"

SMALL_FILES = [
    "config.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "sentencepiece.bpe.model",
    "tokenizer.json",
    "generation_config.json",
]


def step(msg: str) -> None:
    print(f"\n--- {msg} ---", flush=True)


def main() -> int:
    step("1. 캐시만으로 모델 가중치 접근 가능한가 (local_files_only)")
    try:
        p = hf_hub_download(REPO, "pytorch_model.bin", local_files_only=True)
        print(f"OK  캐시에서 해결됨: {p}")
        weights_ok = True
    except Exception as exc:
        print(f"NG  캐시로 해결 안 됨 -> {type(exc).__name__}: {str(exc)[:200]}")
        weights_ok = False

    step("2. 작은 파일(토크나이저 등) 내려받기")
    for name in SMALL_FILES:
        try:
            hf_hub_download(REPO, name)
            print(f"OK  {name}")
        except Exception as exc:
            print(f"NG  {name} -> {type(exc).__name__}: {str(exc)[:120]}")

    step("3. 토크나이저 로딩 (다운로드 금지)")
    try:
        from transformers import AutoTokenizer

        tok = AutoTokenizer.from_pretrained(REPO, local_files_only=True)
        print(f"OK  토크나이저 로딩 성공 (vocab={tok.vocab_size})")
    except Exception as exc:
        print(f"NG  {type(exc).__name__}: {str(exc)[:200]}")
        return 1

    if not weights_ok:
        print("\n결론: 가중치 blob 이 캐시에 없어 2.4GB 재다운로드가 필요하다.")
        return 2

    step("4. 모델 로딩 (다운로드 금지)")
    try:
        from transformers import AutoModelForSeq2SeqLM

        AutoModelForSeq2SeqLM.from_pretrained(REPO, local_files_only=True)
        print("OK  모델 로딩 성공 — 재다운로드 불필요")
    except Exception as exc:
        print(f"NG  {type(exc).__name__}: {str(exc)[:300]}")
        return 3

    print("\n결론: 캐시만으로 NLLB 사용 가능.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
