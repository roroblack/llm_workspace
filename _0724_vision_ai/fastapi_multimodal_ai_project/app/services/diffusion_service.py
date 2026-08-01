"""한국어/영어 프롬프트를 해석하여 Stable Diffusion 이미지로 변환하는 서비스입니다.

이미지 캡셔닝 서비스와 STT 서비스는 변경하지 않습니다. 이 모듈은 이미지 생성 요청만
처리하며, 한국어 프롬프트를 영어로 번역하고 장면 의미를 유지하는 품질 키워드를 추가합니다.
"""

# 정규식은 입력 언어 판별과 불필요한 공백 정리에 사용합니다.
import re

# 여러 요청이 동시에 프롬프트 번역 토크나이저를 만들지 않도록 잠금을 사용합니다.
from threading import Lock

# 파일 이름 충돌을 막기 위해 UUID를 사용합니다.
from uuid import uuid4

# PyTorch 난수 생성기와 추론 전용 모드를 사용합니다.
import torch

# 생성 이미지 저장 경로와 기본 생성 설정을 가져옵니다.
from app.config import GENERATED_DIR, settings

# Stable Diffusion 및 기존 NLLB 모델을 관리하는 클래스를 가져옵니다.
from app.services.model_manager import ModelManager


# 한국어 프롬프트 번역용 토크나이저는 이미지 생성 기능에서만 별도로 관리합니다.
# 번역 모델 가중치는 기존 NLLB 모델을 재사용하므로 같은 대형 모델을 두 번 로딩하지 않습니다.
_prompt_translation_tokenizer = None
_prompt_translation_lock = Lock()


# 사용자가 별도 제외 프롬프트를 입력하지 않아도 적용되는 기본 품질 저하 방지 항목입니다.
DEFAULT_NEGATIVE_PROMPT = (
    "worst quality, low quality, low resolution, blurry, out of focus, "
    "deformed, disfigured, malformed, bad anatomy, bad proportions, "
    "duplicate, extra limbs, extra fingers, missing fingers, cropped, "
    "text, letters, caption, subtitle, watermark, signature, logo, jpeg artifacts"
)


# 장면의 핵심 의미를 바꾸지 않으면서 해상도와 표현 완성도를 높이는 공통 키워드입니다.
QUALITY_SUFFIX = (
    "highly detailed, coherent composition, accurate subject relationships, "
    "natural lighting, sharp focus, high quality"
)


def _contains_korean(text: str) -> bool:
    """문자열에 한글 완성형 또는 자모가 포함되어 있는지 검사합니다."""

    # 한글 음절, 자모 영역 중 하나라도 발견되면 한국어 입력으로 판단합니다.
    return bool(re.search(r"[가-힣ㄱ-ㅎㅏ-ㅣ]", text))


def _get_prompt_translation_tokenizer():
    """한국어 입력용 NLLB 토크나이저를 최초 한 번만 로딩합니다."""

    # 함수 안에서 전역 캐시 변수에 값을 저장할 것임을 선언합니다.
    global _prompt_translation_tokenizer

    # 이미 준비된 토크나이저가 있으면 즉시 재사용합니다.
    if _prompt_translation_tokenizer is not None:
        return _prompt_translation_tokenizer

    # 동시 요청에서도 토크나이저가 한 번만 생성되도록 잠금을 획득합니다.
    with _prompt_translation_lock:
        # 잠금을 기다리는 동안 다른 요청이 만들었는지 다시 확인합니다.
        if _prompt_translation_tokenizer is None:
            # 실제 이미지 생성 요청이 들어왔을 때만 transformers 클래스를 가져옵니다.
            from transformers import AutoTokenizer

            # 한국어를 입력 언어로 지정한 별도 토크나이저를 로딩합니다.
            _prompt_translation_tokenizer = AutoTokenizer.from_pretrained(
                settings.translation_model_id,
                src_lang="kor_Hang",
                use_fast=True,
            )

    # 준비된 한국어 입력용 토크나이저를 반환합니다.
    return _prompt_translation_tokenizer


def _translate_korean_prompt(korean_prompt: str) -> str:
    """NLLB를 사용해 한국어 이미지 생성 프롬프트를 영어로 번역합니다."""

    # 이미지 캡셔닝이 사용하던 NLLB 모델 가중치를 그대로 재사용합니다.
    # 별도의 한국어 입력용 토크나이저만 사용하므로 캡셔닝 토크나이저 설정은 바뀌지 않습니다.
    _, translation_model = ModelManager.get_translation_components()
    tokenizer = _get_prompt_translation_tokenizer()

    # 긴 문장을 무제한 전달하지 않고 이미지 프롬프트에 충분한 길이로 토큰화합니다.
    encoded = tokenizer(
        korean_prompt,
        return_tensors="pt",
        truncation=True,
        max_length=192,
    )

    # 입력 텐서를 NLLB 모델이 위치한 CPU 또는 CUDA 장치로 이동합니다.
    encoded = {
        name: tensor.to(ModelManager.torch_device())
        for name, tensor in encoded.items()
    }

    # 출력 문장을 영어로 강제하기 위한 NLLB 영어 언어 토큰 ID를 구합니다.
    english_token_id = tokenizer.convert_tokens_to_ids("eng_Latn")

    # 빔 탐색으로 객체, 수식어, 행동 관계가 보존되도록 영어 문장을 생성합니다.
    with torch.inference_mode():
        output_ids = translation_model.generate(
            **encoded,
            forced_bos_token_id=english_token_id,
            num_beams=5,
            max_new_tokens=192,
            early_stopping=True,
            no_repeat_ngram_size=2,
            repetition_penalty=1.08,
        )

    # 토큰 ID를 영어 문자열로 복원합니다.
    translated = tokenizer.batch_decode(output_ids, skip_special_tokens=True)[0]

    # SentencePiece 공백 기호와 연속 공백을 정리합니다.
    translated = re.sub(r"\s+", " ", translated.replace("▁", " ")).strip()

    # 번역 결과가 비어 있으면 잘못된 이미지를 생성하지 않도록 오류를 발생시킵니다.
    if not translated:
        raise ValueError("한국어 프롬프트를 영어 이미지 프롬프트로 변환하지 못했습니다.")

    # 이미지 모델에 전달하기 쉽도록 문장 끝 마침표만 제거합니다.
    return translated.rstrip(". ")


def _build_generation_prompt(user_prompt: str) -> tuple[str, str]:
    """사용자 원문과 장면 의미를 보존한 최종 영어 프롬프트를 만듭니다."""

    # 줄바꿈과 중복 공백을 하나로 합쳐 입력 문장을 정규화합니다.
    cleaned_prompt = re.sub(r"\s+", " ", user_prompt).strip()

    # 한국어가 포함되어 있으면 NLLB로 영어 번역하고, 아니면 원문을 그대로 사용합니다.
    translated_prompt = (
        _translate_korean_prompt(cleaned_prompt)
        if _contains_korean(cleaned_prompt)
        else cleaned_prompt
    )

    # 사용자가 지정한 장면을 가장 앞에 두고 품질 키워드는 뒤에 추가합니다.
    # 이 순서는 품질 키워드가 핵심 객체와 행동을 덮어쓰는 현상을 줄입니다.
    enhanced_prompt = f"{translated_prompt}, {QUALITY_SUFFIX}"

    # 화면 표시와 디버깅을 위해 번역 문장과 실제 모델 입력 문장을 함께 반환합니다.
    return translated_prompt, enhanced_prompt


def _merge_negative_prompt(user_negative_prompt: str) -> str:
    """기본 제외 항목과 사용자가 지정한 제외 프롬프트를 중복 없이 합칩니다."""

    # 쉼표 단위로 기본 항목과 사용자 항목을 순서대로 수집합니다.
    candidates = DEFAULT_NEGATIVE_PROMPT.split(",")
    candidates.extend((user_negative_prompt or "").split(","))

    # 대소문자가 다른 동일 항목도 한 번만 남기기 위한 집합입니다.
    seen: set[str] = set()
    merged: list[str] = []

    # 원래 순서를 유지하면서 빈 항목과 중복 항목을 제거합니다.
    for candidate in candidates:
        item = candidate.strip()
        key = item.lower()
        if item and key not in seen:
            seen.add(key)
            merged.append(item)

    # Stable Diffusion이 읽을 수 있는 쉼표 구분 문자열로 반환합니다.
    return ", ".join(merged)


def generate_image(
    prompt: str,
    negative_prompt: str = DEFAULT_NEGATIVE_PROMPT,
    steps: int | None = None,
    guidance_scale: float | None = None,
    seed: int | None = None,
) -> dict[str, str | int]:
    """프롬프트를 입력받아 요구 장면에 맞는 이미지를 생성하고 저장합니다."""

    # 공백만 입력한 프롬프트는 모델에 전달하지 않고 명확한 오류를 발생시킵니다.
    if not prompt.strip():
        raise ValueError("이미지 생성 프롬프트를 입력해야 합니다.")

    # 사용자가 값을 생략하면 설정 파일의 기본 반복 횟수를 사용합니다.
    inference_steps = steps if steps is not None else settings.default_inference_steps

    # 사용자가 값을 생략하면 설정 파일의 기본 프롬프트 반영 강도를 사용합니다.
    scale = (
        guidance_scale
        if guidance_scale is not None
        else settings.default_guidance_scale
    )

    # 시드가 없으면 PyTorch가 생성한 임의 시드를 32비트 양수 범위로 정리합니다.
    resolved_seed = seed if seed is not None else torch.seed() % (2**31)

    # 한국어 번역과 품질 보강을 거친 최종 프롬프트를 생성합니다.
    translated_prompt, enhanced_prompt = _build_generation_prompt(prompt)

    # 기본 품질 저하 방지 항목과 사용자 제외 항목을 결합합니다.
    final_negative_prompt = _merge_negative_prompt(negative_prompt)

    # Stable Diffusion 파이프라인을 최초 요청 시 로딩합니다.
    pipeline = ModelManager.get_diffusion_pipeline()

    # 파이프라인 실행 장치와 동일한 위치에 재현 가능한 난수 생성기를 만듭니다.
    generator = torch.Generator(device=ModelManager.torch_device()).manual_seed(
        resolved_seed
    )

    # SDXL은 기본 학습 해상도인 1024x1024에서 프롬프트 의미와 구도가 더 안정적입니다.
    image_size = settings.diffusion_image_size

    # 자동 미분을 끈 상태에서 텍스트 조건 기반 이미지를 생성합니다.
    with torch.inference_mode():
        result = pipeline(
            prompt=enhanced_prompt,
            negative_prompt=final_negative_prompt,
            num_inference_steps=inference_steps,
            guidance_scale=scale,
            generator=generator,
            width=image_size,
            height=image_size,
        )

    # 파이프라인 결과에서 첫 번째 PIL 이미지를 선택합니다.
    image = result.images[0]

    # UUID 기반 파일 이름을 만들어 동시 요청 간 덮어쓰기를 방지합니다.
    filename = f"generated_{uuid4().hex}.png"

    # 최종 저장 경로를 구성합니다.
    output_path = GENERATED_DIR / filename

    # PNG 형식으로 이미지를 디스크에 저장합니다.
    image.save(output_path, format="PNG")

    # 생성 이미지 URL과 실제 적용된 프롬프트 정보를 반환합니다.
    return {
        "image_url": f"/media/generated/{filename}",
        "seed": int(resolved_seed),
        "prompt_original": prompt.strip(),
        "prompt_english": translated_prompt,
        "prompt_used": enhanced_prompt,
        "negative_prompt_used": final_negative_prompt,
    }
