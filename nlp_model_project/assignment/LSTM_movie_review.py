# -*- coding: utf-8 -*-
"""
NSMC (네이버 영화 리뷰) 데이터 기반 LSTM 감성 분석 모델 - PyTorch Lightning
영화 리뷰 텍스트의 감성(긍정/부정)을 분류하는 모델입니다.
"""

# ---------------------------------------------------------------------
# 1. 기본 라이브러리 불러오기
# ---------------------------------------------------------------------

import os
import re
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Tuple

# VS Code 실행 시 작업 디렉토리가 프로젝트 루트로 설정되어 상대 경로로 파일을 찾지 못하는 문제 해결
# 스크립트 파일 위치 기준으로 절대 경로를 계산해 Config 데이터 경로에 사용
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------
# 2. 딥러닝 라이브러리 불러오기
# ---------------------------------------------------------------------

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torch.utils.data import random_split
import pytorch_lightning as pl
from torchmetrics.classification import BinaryAccuracy


# ---------------------------------------------------------------------
# 3. 설정값 정의
# ---------------------------------------------------------------------

@dataclass
class Config:
    """프로젝트 전체에서 사용할 설정값을 저장하는 클래스입니다."""

    # NSMC 데이터 파일 경로 (수정: IMDB → NSMC)
    train_data_path: str    = os.path.join(_SCRIPT_DIR, "ratings_train.txt")
    test_data_path: str     = os.path.join(_SCRIPT_DIR, "ratings_test.txt")

    max_len: int            = 200
    max_vocab_size: int     = 20000
    min_freq: int           = 2
    batch_size: int         = 64
    embedding_dim: int      = 128
    hidden_dim: int         = 128
    num_layers: int         = 1
    dropout: float          = 0.3
    learning_rate: float    = 0.001
    max_epochs: int         = 3
    val_ratio: float        = 0.2
    num_workers: int        = 0
    seed: int               = 42


# ---------------------------------------------------------------------
# 4. 텍스트 전처리 함수
# ---------------------------------------------------------------------

def clean_korean_text(text: str) -> str:
    """한글 텍스트를 전처리합니다 (수정: NSMC 한글 처리)."""

    # HTML 태그 제거
    text = re.sub(r"<.*?>", " ", text)

    # 한글과 영문/숫자/문장부호만 유지 (수정: 한글 처리)
    # 한글 유니코드 범위: ㄱ-ㅎ (초성), 가-힣 (완성된 한글)
    text = re.sub(r"[^ㄱ-ㅎ가-힣a-zA-Z0-9!?.,' ]", " ", text)

    # 공백 정규화
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    return text


def tokenize(text: str) -> List[str]:
    """한글 문장을 단어 리스트로 분리합니다 (수정: clean_korean_text 호출)."""
    return clean_korean_text(text).split()


# ---------------------------------------------------------------------
# 5. NSMC 데이터 로드 함수
# ---------------------------------------------------------------------


def load_data(config: Config) -> Tuple[List[Tuple[str, int]], List[Tuple[str, int]]]:
    """NSMC (네이버 영화 리뷰) 데이터를 로드합니다 (수정: NSMC 파일 포맷)."""

    print("[데이터 로드] NSMC 데이터셋을 로드합니다.")

    train_samples = []
    test_samples = []

    # 훈련 데이터 로드 (수정: NSMC 파일 포맷 - id\tdocument\tlabel)
    try:
        with open(config.train_data_path, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f):
                if idx == 0:
                    continue

                parts = line.strip().split('\t')
                
                if len(parts) == 3:
                    _, text, label = parts
                    train_samples.append((text, int(label)))
                
                if idx % 10000 == 0 and idx > 0:
                    print(f"  훈련 데이터: {idx}개 로드됨...")

    except Exception as e:
        print(f"[경고] 훈련 데이터 로드 실패: {e}")
        return [], []

    # 테스트 데이터 로드 (수정: NSMC 파일 포맷 - id\tdocument\tlabel)
    try:
        with open(config.test_data_path, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f):
                if idx == 0:
                    continue

                parts = line.strip().split('\t')
                
                if len(parts) == 3:
                    _, text, label = parts
                    test_samples.append((text, int(label)))
                
                if idx % 10000 == 0 and idx > 0:
                    print(f"  테스트 데이터: {idx}개 로드됨...")
                    
    except Exception as e:
        print(f"[경고] 테스트 데이터 로드 실패: {e}")
        return [], []

    print(f"[데이터 로드 완료] train={len(train_samples)}, test={len(test_samples)}")
    return train_samples, test_samples


# ---------------------------------------------------------------------
# 6. Vocabulary 생성 함수
# ---------------------------------------------------------------------

def build_vocab(samples: List[Tuple[str, int]], config: Config) -> Dict[str, int]:
    """훈련 데이터에서 단어 사전을 만듭니다."""

    counter: Counter = Counter()

    for text, _ in samples:
        counter.update(tokenize(text))

    word_to_index: Dict[str, int] = {"<pad>": 0, "<unk>": 1}

    for word, freq in counter.most_common(config.max_vocab_size - len(word_to_index)):
        if freq < config.min_freq:
            continue
        if word not in word_to_index:
            word_to_index[word] = len(word_to_index)

    print(f"[Vocabulary 생성 완료] 단어 수: {len(word_to_index)}")
    return word_to_index


def encode_text(text: str, word_to_index: Dict[str, int], max_len: int) -> torch.Tensor:
    """문장 하나를 고정 길이 정수 텐서로 변환합니다."""

    tokens = tokenize(text)
    token_ids = [word_to_index.get(token, word_to_index["<unk>"]) for token in tokens]
    token_ids = token_ids[:max_len]

    if len(token_ids) < max_len:
        token_ids = token_ids + [word_to_index["<pad>"]] * (max_len - len(token_ids))

    return torch.tensor(token_ids, dtype=torch.long)


# ---------------------------------------------------------------------
# 7. Dataset 클래스 정의
# ---------------------------------------------------------------------

class NSMCDataset(Dataset):
    """NSMC 리뷰 텍스트와 라벨을 PyTorch Dataset 형태로 제공하는 클래스입니다."""

    def __init__(self, samples: List[Tuple[str, int]], word_to_index: Dict[str, int], max_len: int):
        self.samples = samples
        self.word_to_index = word_to_index
        self.max_len = max_len

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> Tuple[torch.Tensor, torch.Tensor]:
        text, label = self.samples[index]
        input_ids = encode_text(text, self.word_to_index, self.max_len)
        label_tensor = torch.tensor(label, dtype=torch.long)
        return input_ids, label_tensor


# ---------------------------------------------------------------------
# 8. LightningDataModule 정의
# ---------------------------------------------------------------------

class NSMCDataModule(pl.LightningDataModule):
    """데이터 준비와 DataLoader 생성을 담당하는 Lightning DataModule입니다."""

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.word_to_index: Dict[str, int] = {}
        self.train_dataset = None
        self.val_dataset = None
        self.test_dataset = None

    def prepare_data(self) -> None:
        pass

    def setup(self, stage: str = None) -> None:
        train_samples, test_samples = load_data(self.config)
        self.word_to_index = build_vocab(train_samples, self.config)
        full_train_dataset = NSMCDataset(train_samples, self.word_to_index, self.config.max_len)
        self.test_dataset = NSMCDataset(test_samples, self.word_to_index, self.config.max_len)

        val_size = int(len(full_train_dataset) * self.config.val_ratio)
        train_size = len(full_train_dataset) - val_size
        generator = torch.Generator().manual_seed(self.config.seed)

        self.train_dataset, self.val_dataset = random_split(
            full_train_dataset,
            [train_size, val_size],
            generator=generator,
        )

        print(f"[Dataset 준비 완료] train={len(self.train_dataset)}, val={len(self.val_dataset)}, test={len(self.test_dataset)}")

    def train_dataloader(self) -> DataLoader:
        return DataLoader(
            self.train_dataset,
            batch_size=self.config.batch_size,
            shuffle=True,
            num_workers=self.config.num_workers,
        )

    def val_dataloader(self) -> DataLoader:
        return DataLoader(
            self.val_dataset,
            batch_size=self.config.batch_size,
            shuffle=False,
            num_workers=self.config.num_workers,
        )

    def test_dataloader(self) -> DataLoader:
        return DataLoader(
            self.test_dataset,
            batch_size=self.config.batch_size,
            shuffle=False,
            num_workers=self.config.num_workers,
        )


# ---------------------------------------------------------------------
# 9. LSTM 모델 정의
# ---------------------------------------------------------------------

class LSTMClassifier(pl.LightningModule):
    """영화 리뷰 감성 분석을 위한 LSTM 분류 모델입니다."""

    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int,
        hidden_dim: int,
        num_layers: int,
        dropout: float,
        learning_rate: float,
        pad_index: int = 0,
    ):
        super().__init__()
        self.save_hyperparameters()
        self.learning_rate = learning_rate

        self.embedding = nn.Embedding(
            num_embeddings=vocab_size,
            embedding_dim=embedding_dim,
            padding_idx=pad_index,
        )

        self.lstm = nn.LSTM(
            input_size=embedding_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
            bidirectional=False,
        )

        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(hidden_dim, 2)
        self.loss_fn = nn.CrossEntropyLoss()

        self.train_acc = BinaryAccuracy()
        self.val_acc = BinaryAccuracy()
        self.test_acc = BinaryAccuracy()

    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        embedded = self.embedding(input_ids)
        output, (hidden, cell) = self.lstm(embedded)
        sentence_vector = hidden[-1]
        sentence_vector = self.dropout(sentence_vector)
        logits = self.classifier(sentence_vector)
        return logits

    def _shared_step(self, batch, stage: str):
        input_ids, labels = batch
        logits = self(input_ids)
        loss = self.loss_fn(logits, labels)
        preds = torch.argmax(logits, dim=1)

        if stage == "train":
            acc = self.train_acc(preds, labels)
        elif stage == "val":
            acc = self.val_acc(preds, labels)
        else:
            acc = self.test_acc(preds, labels)

        self.log(f"{stage}_loss", loss, prog_bar=True, on_step=False, on_epoch=True)
        self.log(f"{stage}_acc", acc, prog_bar=True, on_step=False, on_epoch=True)

        return loss

    def training_step(self, batch, batch_idx):
        return self._shared_step(batch, "train")

    def validation_step(self, batch, batch_idx):
        self._shared_step(batch, "val")

    def test_step(self, batch, batch_idx):
        self._shared_step(batch, "test")

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=self.learning_rate)
        return optimizer


# ---------------------------------------------------------------------
# 10. 예측 함수
# ---------------------------------------------------------------------

def predict_sentiment(model: LSTMClassifier, text: str, word_to_index: Dict[str, int], config: Config) -> Tuple[str, float]:
    """학습된 모델로 문장 하나의 감성을 예측합니다."""

    model.eval()

    with torch.no_grad():
        input_ids = encode_text(text, word_to_index, config.max_len)
        input_ids = input_ids.unsqueeze(0)
        input_ids = input_ids.to(model.device)
        logits = model(input_ids)
        probabilities = torch.softmax(logits, dim=1)
        pred_id = torch.argmax(probabilities, dim=1).item()
        confidence = probabilities[0, pred_id].item()

    label = "positive" if pred_id == 1 else "negative"
    return label, confidence


# ---------------------------------------------------------------------
# 11. main 함수
# ---------------------------------------------------------------------

def main() -> None:
    """전체 실행 흐름을 담당하는 main 함수입니다."""

    config = Config()
    pl.seed_everything(config.seed, workers=True)
    data_module = NSMCDataModule(config)
    data_module.setup(stage="fit")
    vocab_size = len(data_module.word_to_index)

    model = LSTMClassifier(
        vocab_size      =   vocab_size,
        embedding_dim   =   config.embedding_dim,
        hidden_dim      =   config.hidden_dim,
        num_layers      =   config.num_layers,
        dropout         =   config.dropout,
        learning_rate   =   config.learning_rate,
        pad_index       =   data_module.word_to_index["<pad>"],
    )

    accelerator = "gpu" if torch.cuda.is_available() else "cpu"

    trainer = pl.Trainer(
        max_epochs=config.max_epochs,
        accelerator=accelerator,
        devices=1,
        log_every_n_steps=10,
        enable_checkpointing=False,
    )

    trainer.fit(model, datamodule=data_module)

    model_save_path = "models/nsmc_lstm_model.pt"
    os.makedirs("models", exist_ok=True)
    torch.save({
        'model_state_dict': model.state_dict(),
        'config': config,
        'word_to_index': data_module.word_to_index,
    }, model_save_path)
    print(f"\n[Model Saved] {model_save_path}")

    try:
        trainer.test(model, datamodule=data_module)
    except Exception as e:
        print(f"Test error (non-critical): {str(e)[:100]}")

    examples = [
        "이 영화는 정말 훌륭하고 배우들의 연기가 뛰어났다.",
        "너무 지루하고 스토리가 형편없었다.",
    ]

    print("\n[Prediction Examples]")
    try:
        for text in examples:
            label, confidence = predict_sentiment(model, text, data_module.word_to_index, config)
            print(f"Text: {text}")
            print(f"Prediction: {label}, Confidence: {confidence:.4f}\n")
    except Exception as e:
        print(f"Prediction error (non-critical): {str(e)[:100]}")


# ---------------------------------------------------------------------
# 12. 프로그램 시작 지점
# ---------------------------------------------------------------------

if __name__ == "__main__":
    main()
