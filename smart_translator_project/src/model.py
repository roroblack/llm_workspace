"""문자 단위 Transformer 번역 모델을 정의하는 파일입니다."""

# ============================================================================
# [변경 요약] Seq2Seq(RNN/LSTM) → Transformer
# ----------------------------------------------------------------------------
# 이전(Seq2Seq): Encoder LSTM이 문장 전체를 하나의 (hidden, cell) 벡터로 압축하고,
#   Decoder LSTM이 그 벡터를 초기 상태로 받아 한 글자씩 순차 생성했습니다.
#   → 순차 처리라 문장이 길어지면 앞쪽 정보가 희미해지고(장기 의존성 한계),
#     시점마다 상태를 넘겨야 해서 학습 병렬화가 어렵습니다.
#
# 이후(Transformer): 순환(recurrence)을 없애고 Self-Attention으로 문장 안 모든
#   위치가 서로를 직접 참조합니다. 그 결과 아래 4가지가 새로 필요/변경됩니다.
#     1) 위치 임베딩(position_embedding): 순서 정보가 사라지므로 직접 더해 줌
#     2) padding mask: PAD 칸을 attention에서 제외
#     3) causal(future) mask: 디코더가 미래 정답을 미리 보지 못하게 차단
#     4) 학습 시 전체 시퀀스를 한 번에 병렬 계산 (LSTM처럼 hidden 전달 없음)
# ============================================================================

import math

import torch
import torch.nn as nn


class TransformerTranslator(nn.Module):
    """문자 단위 영어<->한국어 번역을 위한 Transformer encoder-decoder 모델입니다."""

    def __init__(
        self,
        vocab_size,
        d_model,
        nhead,
        num_encoder_layers,
        num_decoder_layers,
        dim_feedforward,
        dropout,
        pad_index=0,
        max_seq_len=128,
    ):
        super().__init__()

        self.vocab_size = vocab_size
        self.d_model = d_model
        self.pad_index = pad_index
        self.max_seq_len = max_seq_len

        # [변경점] Seq2Seq는 인코더/디코더가 각자 nn.Embedding + nn.LSTM을 가졌습니다.
        # Transformer에서는 임베딩만 따로 두고, 순서 처리는 아래 position_embedding과
        # self.transformer(어텐션)가 담당합니다.
        self.source_embedding = nn.Embedding(vocab_size, d_model, padding_idx=pad_index)
        self.target_embedding = nn.Embedding(vocab_size, d_model, padding_idx=pad_index)
        # [신규] 위치 임베딩. LSTM은 순서를 순차 처리로 자연히 알았지만, 어텐션은
        # 순서 개념이 없으므로 각 위치 벡터를 학습해 토큰 임베딩에 더해 줍니다.
        self.position_embedding = nn.Embedding(max_seq_len, d_model)
        self.dropout = nn.Dropout(dropout)

        # [변경점] Encoder LSTM + Decoder LSTM 두 모듈을 nn.Transformer 하나가 대체합니다.
        # (내부에 Self-Attention 기반 encoder/decoder layer가 모두 들어 있습니다.)
        self.transformer = nn.Transformer(
            d_model=d_model,
            nhead=nhead,
            num_encoder_layers=num_encoder_layers,
            num_decoder_layers=num_decoder_layers,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
        )
        self.output_layer = nn.Linear(d_model, vocab_size)

    def _add_positions(self, token_ids, embedding):
        """토큰 임베딩에 위치 임베딩을 더합니다."""
        batch_size, seq_len = token_ids.shape
        if seq_len > self.max_seq_len:
            raise ValueError(
                f"입력 길이 {seq_len}이 MAX_SEQ_LEN({self.max_seq_len})보다 깁니다."
            )

        positions = torch.arange(seq_len, device=token_ids.device)
        positions = positions.unsqueeze(0).expand(batch_size, seq_len)
        token_vectors = embedding(token_ids) * math.sqrt(self.d_model)
        position_vectors = self.position_embedding(positions)
        return self.dropout(token_vectors + position_vectors)

    def make_padding_mask(self, token_ids):
        """PAD 토큰 위치를 attention에서 제외하기 위한 boolean mask를 만듭니다."""
        # [신규] Seq2Seq에서는 pad_sequence로 길이만 맞추면 됐지만(LSTM이 PAD를 그냥
        # 통과), 어텐션은 모든 위치를 참조하므로 PAD를 명시적으로 가려 줘야 합니다.
        return token_ids.eq(self.pad_index)

    @staticmethod
    def make_future_mask(size, device):
        """디코더가 미래 정답 문자를 미리 보지 못하도록 causal mask를 만듭니다."""
        # [신규] LSTM 디코더는 구조상 과거만 보지만, 어텐션은 뒤 토큰까지 한 번에
        # 볼 수 있으므로 학습 시 미래 정답을 가리는 삼각 마스크가 반드시 필요합니다.
        return torch.triu(
            torch.ones(size, size, dtype=torch.bool, device=device),
            diagonal=1,
        )

    def forward(self, source, decoder_input):
        """source와 decoder_input을 받아 각 출력 위치의 문자 logits를 반환합니다."""
        # [변경점] Seq2Seq forward는 hidden, cell = encoder(source) 후 그 상태를
        # 디코더에 넘겨주는 2단계였습니다. Transformer는 (임베딩+위치) → 마스크 3종 →
        # self.transformer 한 번 호출로 전체 시퀀스를 병렬 처리합니다.
        source_embedded = self._add_positions(source, self.source_embedding)
        target_embedded = self._add_positions(decoder_input, self.target_embedding)

        source_padding_mask = self.make_padding_mask(source)
        target_padding_mask = self.make_padding_mask(decoder_input)
        target_future_mask = self.make_future_mask(decoder_input.size(1), decoder_input.device)

        transformer_output = self.transformer(
            src=source_embedded,
            tgt=target_embedded,
            tgt_mask=target_future_mask,
            src_key_padding_mask=source_padding_mask,
            tgt_key_padding_mask=target_padding_mask,
            memory_key_padding_mask=source_padding_mask,
        )
        return self.output_layer(transformer_output)


def build_model(
    vocab_size,
    d_model,
    nhead,
    num_encoder_layers,
    num_decoder_layers,
    dim_feedforward,
    dropout,
    pad_index=0,
    max_seq_len=128,
):
    """설정값을 받아 Transformer 번역 모델을 생성하는 도우미 함수입니다."""
    return TransformerTranslator(
        vocab_size=vocab_size,
        d_model=d_model,
        nhead=nhead,
        num_encoder_layers=num_encoder_layers,
        num_decoder_layers=num_decoder_layers,
        dim_feedforward=dim_feedforward,
        dropout=dropout,
        pad_index=pad_index,
        max_seq_len=max_seq_len,
    )
