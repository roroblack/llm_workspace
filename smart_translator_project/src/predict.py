"""저장된 Transformer 모델을 불러와 입력 문장을 번역하는 파일입니다."""

from functools import lru_cache

import torch

from src.config import (
    DATA_PATH,
    MODEL_PATH,
    META_PATH,
    MODEL_TYPE,
    MAX_OUTPUT_LEN,
    PAD_TOKEN,
    SOS_TOKEN,
    EOS_TOKEN,
    UNK_TOKEN,
)
from src.data_utils import (
    encode_text,
    detect_language,
    build_directional_source,
    normalize_text,
    load_exact_translation_lookup,
)
from src.model import build_model


def get_device():
    """GPU가 있으면 GPU를, 없으면 CPU를 사용하도록 장치를 선택합니다."""
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def checkpoint_is_current():
    """저장된 체크포인트가 현재 Transformer 구현과 호환되는지 확인합니다."""
    if not MODEL_PATH.exists() or not META_PATH.exists():
        return False

    try:
        meta = torch.load(META_PATH, map_location="cpu")
    except Exception:
        return False

    return meta.get("model_type") == MODEL_TYPE


@lru_cache(maxsize=1)
def _exact_translation_lookup():
    """CSV에 있는 원문과 정확히 일치하는 문장용 번역 사전을 캐싱합니다."""
    return load_exact_translation_lookup(DATA_PATH)


def lookup_exact_translation(text):
    """학습 CSV에 정확히 있는 문장이면 정답 번역을 반환합니다."""
    language = detect_language(text)
    normalized = normalize_text(text)
    return _exact_translation_lookup().get((language, normalized))


def load_model():
    """저장된 Transformer 모델 가중치와 문자 사전을 불러옵니다."""
    if not MODEL_PATH.exists() or not META_PATH.exists():
        raise FileNotFoundError(
            "학습된 모델이 없습니다. 먼저 `python -m src.train` 으로 학습을 실행하세요."
        )

    device = get_device()
    meta = torch.load(META_PATH, map_location=device)
    if meta.get("model_type") != MODEL_TYPE:
        raise ValueError(
            "저장된 모델이 현재 Transformer 구조와 맞지 않습니다. "
            "`python -m src.train` 으로 다시 학습하세요."
        )

    char2idx = meta["char2idx"]
    idx2char = meta["idx2char"]

    model = build_model(
        vocab_size=meta["vocab_size"],
        d_model=meta["d_model"],
        nhead=meta["nhead"],
        num_encoder_layers=meta["num_encoder_layers"],
        num_decoder_layers=meta["num_decoder_layers"],
        dim_feedforward=meta["dim_feedforward"],
        dropout=meta["dropout"],
        pad_index=meta["pad_index"],
        max_seq_len=meta["max_seq_len"],
    ).to(device)

    model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    model.eval()

    return model, char2idx, idx2char


def translate(text, model, char2idx, idx2char, max_len=None, use_exact_lookup=True):
    """입력 문장의 언어를 판별한 뒤 반대 언어로 번역한 문자열을 반환합니다."""
    max_len = MAX_OUTPUT_LEN if max_len is None else max_len

    if use_exact_lookup:
        exact_translation = lookup_exact_translation(text)
        if exact_translation is not None:
            return exact_translation

    device = get_device()
    model.eval()

    language = detect_language(text)
    source_text = build_directional_source(text, language)
    source_ids = encode_text(source_text, char2idx, add_eos=True)
    source_tensor = torch.tensor([source_ids], dtype=torch.long, device=device)

    pad_index = char2idx[PAD_TOKEN]
    sos_index = char2idx[SOS_TOKEN]
    eos_index = char2idx[EOS_TOKEN]

    # [변경점] Seq2Seq 추론은 hidden, cell = encoder(...) 후 LSTM 상태를 시점마다
    # 넘겨받으며 한 글자씩 생성했습니다. Transformer는 넘겨줄 상태가 없으므로,
    # 지금까지 생성한 토큰열(generated)을 매 스텝 통째로 다시 입력해 다음 글자를 예측합니다.
    generated = torch.tensor([[sos_index]], dtype=torch.long, device=device)
    result_chars = []

    with torch.no_grad():
        for _ in range(max_len):
            # [변경점] 매 스텝 (source, 지금까지 생성분) 전체를 모델에 넣고,
            # 마지막 위치 출력만 꺼내 다음 글자를 고릅니다(greedy).
            output = model(source_tensor, generated)
            next_index = output[:, -1, :].argmax(dim=-1).item()

            if next_index in {eos_index, pad_index}:
                break

            next_char = idx2char.get(next_index, UNK_TOKEN)
            if next_char not in {PAD_TOKEN, SOS_TOKEN, EOS_TOKEN}:
                result_chars.append(next_char)

            # [변경점] Seq2Seq는 다음 입력 토큰 1개만 넘겼지만, Transformer는 방금 예측한
            # 글자를 generated 뒤에 이어 붙여 '누적된 시퀀스'를 다음 스텝 입력으로 씁니다.
            next_token = torch.tensor([[next_index]], dtype=torch.long, device=device)
            generated = torch.cat([generated, next_token], dim=1)

    return "".join(result_chars).strip()


if __name__ == "__main__":
    loaded_model, loaded_char2idx, loaded_idx2char = load_model()
    for sample in ["hello", "thank you", "안녕하세요", "감사합니다"]:
        translated = translate(sample, loaded_model, loaded_char2idx, loaded_idx2char)
        print(f"{sample} -> {translated}")
