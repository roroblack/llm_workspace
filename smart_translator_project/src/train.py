"""번역 데이터를 학습하여 Transformer 모델과 문자 사전을 저장하는 실행 스크립트입니다."""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from src.config import (
    DATA_PATH,
    MODEL_PATH,
    META_PATH,
    MODEL_TYPE,
    D_MODEL,
    NHEAD,
    NUM_ENCODER_LAYERS,
    NUM_DECODER_LAYERS,
    DIM_FEEDFORWARD,
    DROPOUT,
    MAX_SEQ_LEN,
    EPOCHS,
    BATCH_SIZE,
    LEARNING_RATE,
    PAD_TOKEN,
)
from src.data_utils import (
    load_translation_pairs,
    build_vocab,
    TranslationDataset,
    collate_batch,
)
from src.model import build_model


def get_device():
    """GPU가 있으면 GPU를, 없으면 CPU를 사용하도록 장치를 선택합니다."""
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def train_model(epochs=None, batch_size=None, learning_rate=None, verbose=True):
    """데이터를 불러와 Transformer 번역 모델을 학습하고 모델과 사전을 저장합니다."""
    epochs = EPOCHS if epochs is None else epochs
    batch_size = BATCH_SIZE if batch_size is None else batch_size
    learning_rate = LEARNING_RATE if learning_rate is None else learning_rate

    device = get_device()

    pairs = load_translation_pairs(DATA_PATH)
    char2idx, idx2char = build_vocab(pairs)
    vocab_size = len(char2idx)
    pad_index = char2idx[PAD_TOKEN]

    dataset = TranslationDataset(pairs, char2idx)
    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=collate_batch,
    )

    # [변경점] Seq2Seq는 build_model(vocab_size, EMBED_SIZE, HIDDEN_SIZE, pad_index)로
    # 만들었지만, 이제 Transformer 하이퍼파라미터(d_model/nhead/레이어 수 등)를 넘깁니다.
    model = build_model(
        vocab_size=vocab_size,
        d_model=D_MODEL,
        nhead=NHEAD,
        num_encoder_layers=NUM_ENCODER_LAYERS,
        num_decoder_layers=NUM_DECODER_LAYERS,
        dim_feedforward=DIM_FEEDFORWARD,
        dropout=DROPOUT,
        pad_index=pad_index,
        max_seq_len=MAX_SEQ_LEN,
    ).to(device)

    # 손실 함수는 동일(PAD 위치 제외). [변경점] 옵티마이저는 Adam → AdamW로 바꿨습니다.
    # AdamW는 가중치 감쇠를 분리 적용해 Transformer 학습에서 더 흔히 쓰입니다.
    criterion = nn.CrossEntropyLoss(ignore_index=pad_index)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0

        for source, decoder_input, decoder_target in loader:
            source = source.to(device)
            decoder_input = decoder_input.to(device)
            decoder_target = decoder_target.to(device)

            optimizer.zero_grad()
            predictions = model(source, decoder_input)
            output_dim = predictions.size(-1)
            loss = criterion(
                predictions.reshape(-1, output_dim),
                decoder_target.reshape(-1),
            )
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / max(1, len(loader))
        if verbose and (epoch == 1 or epoch % 25 == 0 or epoch == epochs):
            print(f"Epoch [{epoch:03d}/{epochs}] loss={avg_loss:.4f}", flush=True)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    torch.save(model.state_dict(), MODEL_PATH)
    torch.save(
        {
            "model_type": MODEL_TYPE,
            "char2idx": char2idx,
            "idx2char": idx2char,
            "vocab_size": vocab_size,
            "pad_index": pad_index,
            "d_model": D_MODEL,
            "nhead": NHEAD,
            "num_encoder_layers": NUM_ENCODER_LAYERS,
            "num_decoder_layers": NUM_DECODER_LAYERS,
            "dim_feedforward": DIM_FEEDFORWARD,
            "dropout": DROPOUT,
            "max_seq_len": MAX_SEQ_LEN,
        },
        META_PATH,
    )

    if verbose:
        print("모델 저장 완료:", MODEL_PATH, flush=True)
        print("메타 저장 완료:", META_PATH, flush=True)

    return model, char2idx, idx2char


if __name__ == "__main__":
    train_model()
