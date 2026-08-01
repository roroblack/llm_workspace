"""업로드 이미지에서 영어 캡션과 자연스럽고 정확한 한국어 설명을 생성합니다."""

# 문장 정리와 핵심 객체 검증에 정규식을 사용합니다.
import re

# 이미지 파일을 RGB로 변환하기 위해 PIL Image를 사용합니다.
from PIL import Image

# 모델 추론 시 그래디언트 계산을 끄기 위해 PyTorch를 사용합니다.
import torch

# BLIP 캡셔닝 모델과 NLLB 번역 모델을 지연 로딩하는 관리자를 가져옵니다.
from app.services.model_manager import ModelManager


# 영어 캡션에서 자주 나타나는 핵심 객체와 자연스러운 한국어 표현을 정의합니다.
# NLLB 번역이 실패하거나 핵심 객체를 누락할 때만 보정용으로 사용합니다.
OBJECT_TERMS: dict[str, str] = {
    "person": "사람", "man": "남자", "woman": "여자", "boy": "소년", "girl": "소녀",
    "child": "아이", "dog": "강아지", "puppy": "강아지", "cat": "고양이", "kitten": "새끼 고양이",
    "car": "자동차", "bus": "버스", "truck": "트럭", "bicycle": "자전거", "bike": "자전거",
    "motorcycle": "오토바이", "horse": "말", "bird": "새", "tree": "나무", "bench": "벤치",
    "table": "탁자", "chair": "의자", "street": "거리", "road": "도로", "park": "공원",
}

# 영어 행동 표현을 한국어 진행형 서술어로 변환하는 보정 사전입니다.
ACTION_TERMS: dict[str, str] = {
    "walking": "걷고 있습니다", "running": "달리고 있습니다", "standing": "서 있습니다",
    "sitting": "앉아 있습니다", "holding": "들고 있습니다", "riding": "타고 있습니다",
    "playing": "놀고 있습니다", "looking": "바라보고 있습니다", "eating": "먹고 있습니다",
    "drinking": "마시고 있습니다", "sleeping": "자고 있습니다", "jumping": "뛰어오르고 있습니다",
}


def _clean_english_caption(caption: str) -> str:
    """BLIP 출력의 공백과 문장 부호를 정리합니다."""

    # 줄바꿈과 여러 공백을 하나로 합칩니다.
    cleaned = re.sub(r"\s+", " ", caption).strip()

    # 빈 결과는 정상적인 캡션이 아니므로 명확한 오류를 발생시킵니다.
    if not cleaned:
        raise ValueError("이미지에서 설명 문장을 생성하지 못했습니다.")

    # 문장 첫 글자를 대문자로 바꾸어 번역 모델이 문장 경계를 명확히 인식하게 합니다.
    cleaned = cleaned[0].upper() + cleaned[1:]

    # 문장 끝에 종결 부호가 없으면 마침표를 추가합니다.
    if cleaned[-1] not in ".!?":
        cleaned += "."

    # 정리한 영어 문장을 반환합니다.
    return cleaned


def _clean_korean_caption(caption: str) -> str:
    """한국어 번역 결과를 화면과 TTS에 적합한 문장으로 정리합니다."""

    # SentencePiece 특수 공백과 연속 공백을 일반 공백으로 정리합니다.
    cleaned = re.sub(r"\s+", " ", caption.replace("▁", " ")).strip()

    # 문장 양끝에 남은 따옴표를 제거합니다.
    cleaned = cleaned.strip('"\'“”‘’ ')

    # NLLB가 간혹 붙이는 언어 코드 문자열을 제거합니다.
    cleaned = re.sub(r"^(kor_Hang|한국어)\s*[:：-]?\s*", "", cleaned, flags=re.IGNORECASE)

    # 빈 번역은 후속 보정이 가능하도록 오류로 처리합니다.
    if not cleaned:
        raise ValueError("한국어 번역 결과가 비어 있습니다.")

    # 서술형 수업 서비스에 맞게 지나친 구어체 종결을 자연스러운 높임말로 정리합니다.
    replacements = {
        "하고 있다.": "하고 있습니다.", "걷고 있다.": "걷고 있습니다.",
        "서 있다.": "서 있습니다.", "앉아 있다.": "앉아 있습니다.",
        "보인다.": "보입니다.", "있다.": "있습니다.",
    }
    for source, target in replacements.items():
        if cleaned.endswith(source):
            cleaned = cleaned[: -len(source)] + target
            break

    # 문장 끝에 종결 부호가 없으면 마침표를 추가합니다.
    if cleaned[-1] not in ".!?。":
        cleaned += "."

    # 문장 부호 앞의 불필요한 공백을 제거합니다.
    return re.sub(r"\s+([.!?])", r"\1", cleaned)


def _translate_with_nllb(english_caption: str) -> str:
    """NLLB 모델로 영어 캡션을 한국어로 번역합니다."""

    # NLLB 토크나이저와 번역 모델을 최초 요청 시 한 번만 준비합니다.
    tokenizer, model = ModelManager.get_translation_components()

    # 영어 문장을 모델 입력 텐서로 변환합니다.
    encoded = tokenizer(
        english_caption,
        return_tensors="pt",
        truncation=True,
        max_length=128,
    )

    # 입력 텐서를 번역 모델과 동일한 장치로 이동합니다.
    encoded = {name: tensor.to(ModelManager.torch_device()) for name, tensor in encoded.items()}

    # 한국어 언어 코드의 토큰 ID를 구해 출력 언어를 정확히 고정합니다.
    korean_token_id = tokenizer.convert_tokens_to_ids("kor_Hang")

    # 빔 탐색으로 문장의 객체·행동·관계를 최대한 보존한 한국어 번역을 생성합니다.
    with torch.inference_mode():
        output_ids = model.generate(
            **encoded,
            forced_bos_token_id=korean_token_id,
            num_beams=5,
            max_new_tokens=128,
            early_stopping=True,
            no_repeat_ngram_size=2,
            repetition_penalty=1.1,
        )

    # 토큰 ID를 한국어 문자열로 복원하고 표시용 문장으로 정리합니다.
    translated = tokenizer.batch_decode(output_ids, skip_special_tokens=True)[0]
    return _clean_korean_caption(translated)


def _extract_objects(english_caption: str) -> list[str]:
    """영어 캡션에 실제로 포함된 핵심 객체의 한국어 이름을 순서대로 추출합니다."""

    # 대소문자와 문장 부호 영향을 없앤 검색용 문자열을 만듭니다.
    normalized = re.sub(r"[^a-z0-9\s]", " ", english_caption.lower())

    # 동일 한국어 객체가 중복되지 않도록 리스트에 한 번만 추가합니다.
    found: list[str] = []
    for english, korean in OBJECT_TERMS.items():
        if re.search(rf"\b{re.escape(english)}\b", normalized) and korean not in found:
            found.append(korean)

    # 영어 문장에 실제 등장한 객체 목록을 반환합니다.
    return found


def _translation_preserves_objects(english_caption: str, korean_caption: str) -> bool:
    """영어 캡션의 핵심 객체가 한국어 번역에 보존됐는지 검사합니다."""

    # 영어 원문에서 핵심 객체를 추출합니다.
    expected_objects = _extract_objects(english_caption)

    # 알려진 객체가 없는 문장은 번역 결과를 그대로 신뢰합니다.
    if not expected_objects:
        return True

    # 두 개 이하의 짧은 캡션에서는 모든 객체가 번역에 포함되어야 정확하다고 판단합니다.
    return all(obj in korean_caption for obj in expected_objects)


def _rule_based_caption(english_caption: str) -> str:
    """번역 실패 또는 객체 누락 시 핵심 정보를 보존한 한국어 문장을 만듭니다."""

    # 검색하기 쉽도록 영어 문장을 소문자로 정규화합니다.
    normalized = re.sub(r"[^a-z0-9\s]", " ", english_caption.lower())

    # 캡션에 등장한 객체를 순서대로 추출합니다.
    objects = _extract_objects(english_caption)

    # 캡션에 등장한 첫 번째 행동을 찾습니다.
    action = next(
        (korean for english, korean in ACTION_TERMS.items() if re.search(rf"\b{english}\b", normalized)),
        "보입니다",
    )

    # 사람과 강아지, 목줄 관계는 자주 등장하며 단순 객체 나열보다 관계 표현이 중요합니다.
    if ("사람" in objects or "남자" in objects or "여자" in objects) and "강아지" in objects:
        if "leash" in normalized:
            return "한 사람이 목줄을 한 강아지와 함께 걷고 있습니다."
        return f"한 사람이 강아지와 함께 {action}."

    # 객체가 두 개 이상이면 자연스러운 연결 조사로 함께 설명합니다.
    if len(objects) >= 2:
        return f"사진에는 {objects[0]}과(와) {objects[1]}이(가) 있으며, {objects[0]}이(가) {action}."

    # 객체가 하나이면 해당 객체를 주제로 완전한 문장을 생성합니다.
    if len(objects) == 1:
        return f"사진에는 {objects[0]}이(가) {action}."

    # 사전에 없는 장면도 영어가 섞이지 않는 안전한 문장으로 반환합니다.
    return "사진 속 장면에서 여러 대상과 행동이 보입니다."


def generate_caption(image_path: str) -> dict[str, str]:
    """이미지에서 영어 캡션과 정확한 한국어 설명을 생성합니다."""

    # BLIP 프로세서와 이미지 캡셔닝 모델을 지연 로딩합니다.
    processor, model = ModelManager.get_caption_components()

    # 이미지 파일을 열고 모든 모델이 안정적으로 처리할 수 있는 RGB로 변환합니다.
    with Image.open(image_path) as source_image:
        image = source_image.convert("RGB")

    # PIL 이미지를 BLIP 입력 텐서로 변환합니다.
    inputs = processor(images=image, return_tensors="pt")

    # 입력 텐서를 BLIP 모델과 동일한 CPU 또는 GPU 장치로 이동합니다.
    inputs = {name: tensor.to(ModelManager.torch_device()) for name, tensor in inputs.items()}

    # 빔 탐색으로 주요 객체와 행동을 포함하는 영어 캡션을 생성합니다.
    with torch.inference_mode():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=60,
            num_beams=5,
            min_length=5,
            repetition_penalty=1.15,
        )

    # BLIP 토큰을 영어 문장으로 복원합니다.
    english_caption = _clean_english_caption(
        processor.decode(output_ids[0], skip_special_tokens=True)
    )

    try:
        # NLLB로 영어 캡션을 자연스러운 한국어 문장으로 번역합니다.
        korean_caption = _translate_with_nllb(english_caption)

        # 번역이 핵심 객체를 누락하면 의미 보존형 보정 문장으로 교체합니다.
        if not _translation_preserves_objects(english_caption, korean_caption):
            korean_caption = _rule_based_caption(english_caption)
            translation_method = "nllb_with_semantic_correction"
        else:
            translation_method = "nllb_en_ko"
    except Exception:
        # 모델 다운로드 실패나 메모리 부족에도 서비스가 중단되지 않도록 보정 문장을 사용합니다.
        korean_caption = _rule_based_caption(english_caption)
        translation_method = "semantic_fallback"

    # 영어 원문, 한국어 설명, 처리 방식을 JSON 응답용 사전으로 반환합니다.
    return {
        "caption_en": english_caption,
        "caption_ko": korean_caption,
        "translation_method": translation_method,
    }
