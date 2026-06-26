# -*- coding: utf-8 -*-
"""
    IMDB 영화 리뷰 데이터셋을 사용하여 리뷰 문장이 긍정(pos)인지 부정(neg)인지 분류하는
    LSTM 기반 자연어 처리 모델을 PyTorch Lightning으로 학습합니다.
"""

import torch
import torch.nn as nn
from torch.optim import Adam
from torch.utils.data import Dataset, DataLoader
import pytorch_lightning as pl
from torchmetrics import Accuracy
import os
import re
from collections import defaultdict

# 설정
device = "cuda" if torch.cuda.is_available() else "cpu"
batch_size = 32
seq_len = 200
embedding_dim = 100
hidden_dim = 100
output_dim = 2
num_epochs = 3

# 텍스트 전처리 함수
def clean_text(text):
    text = re.sub(r'<br />', ' ', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = text.lower().split()
    return text


# 복습: Vocabulary 빌드 함수
def build_vocab(texts, vocab_size=5000):
    word_freq = defaultdict(int)
    for text in texts:
        for word in text:
            word_freq[word] += 1

    # 빈도순으로 정렬
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:vocab_size]
    word_to_idx = {word: idx + 2 for idx, (word, _) in enumerate(sorted_words)}
    word_to_idx['<pad>'] = 0
    word_to_idx['<unk>'] = 1

    return word_to_idx


# IMDB 데이터 로드 함수
def load_imdb_data(data_dir='aclImdb', split='train'):
    texts = []
    labels = []

    for sentiment in ['pos', 'neg']:
        path = os.path.join(data_dir, split, sentiment)
        if not os.path.exists(path):
            return None, None

        for filename in os.listdir(path):
            if filename.endswith('.txt'):
                with open(os.path.join(path, filename), 'r', encoding='utf-8') as f:
                    text = f.read()
                    texts.append(clean_text(text))
                    labels.append(0 if sentiment == 'neg' else 1)

    return texts, labels


# 복습: Custom Dataset 클래스
class IMDBDataset(Dataset):
    def __init__(self, texts, labels, word_to_idx, seq_len):
        self.data = []
        self.labels = labels

        for text in texts:
            indices = []
            for word in text[:seq_len]:
                indices.append(word_to_idx.get(word, word_to_idx['<unk>']))

            # 부족한 부분 패딩
            if len(indices) < seq_len:
                indices += [word_to_idx['<pad>']] * (seq_len - len(indices))
            else:
                indices = indices[:seq_len]

            self.data.append(torch.tensor(indices, dtype=torch.long))

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx], self.labels[idx]


# 샘플 데이터 생성 함수 (IMDB 데이터셋이 없을 때)
def create_sample_data(num_samples=1000):
    positive_words = ['good', 'great', 'excellent', 'amazing', 'awesome', 'fantastic', 'wonderful', 'love', 'best', 'brilliant']
    negative_words = ['bad', 'terrible', 'awful', 'horrible', 'worst', 'hate', 'poor', 'disappointing', 'dull', 'boring']

    texts = []
    labels = []

    for i in range(num_samples):
        if i < num_samples // 2:
            # 긍정 리뷰
            text = ' '.join([positive_words[j % len(positive_words)] for j in range(20)])
            labels.append(1)
        else:
            # 부정 리뷰
            text = ' '.join([negative_words[j % len(negative_words)] for j in range(20)])
            labels.append(0)

        texts.append(clean_text(text))

    return texts, labels


print("[데이터 준비 중...]")

# IMDB 데이터 로드 시도
train_texts, train_labels = load_imdb_data(split='train')

# 데이터가 없으면 샘플 데이터 생성
if train_texts is None:
    print("💡 샘플 데이터로 진행합니다.")
    train_texts, train_labels = create_sample_data(num_samples=2000)
    test_texts, test_labels = create_sample_data(num_samples=500)
else:
    test_texts, test_labels = load_imdb_data(split='test')

# Vocabulary 생성
word_to_idx = build_vocab(train_texts)
vocab_size = len(word_to_idx)

print(f"[Vocabulary 크기] {vocab_size}")
print(f"[훈련 샘플 수] {len(train_texts)}")
print(f"[테스트 샘플 수] {len(test_texts)}")

# 데이터셋 생성
train_dataset = IMDBDataset(train_texts, train_labels, word_to_idx, seq_len)
test_dataset = IMDBDataset(test_texts, test_labels, word_to_idx, seq_len)

train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size)


# 복습: PyTorch Lightning 모델 정의
class IMDBLSTMModel(pl.LightningModule):
    def __init__(self, vocab_size, embedding_dim, hidden_dim, output_dim):
        super().__init__()

        # 임베딩 레이어
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)

        # LSTM 레이어
        self.lstm = nn.LSTM(
            embedding_dim,
            hidden_dim,
            num_layers=1,
            batch_first=True,
            dropout=0.3
        )

        # 분류 레이어
        self.fc = nn.Linear(hidden_dim, output_dim)

        # 손실 함수
        self.loss_fn = nn.CrossEntropyLoss()

        # 정확도 메트릭
        self.train_accuracy = Accuracy(task="binary")
        self.val_accuracy = Accuracy(task="binary")

    def forward(self, x):
        # x shape: (batch_size, seq_len)
        embedded = self.embedding(x)  # (batch_size, seq_len, embedding_dim)

        # LSTM 출력
        _, (hidden, _) = self.lstm(embedded)

        # 마지막 타임스텝의 hidden state만 사용
        # 심화학습: 일반적으로 RNN/LSTM에서는 마지막 출력만 분류에 사용
        last_hidden = hidden[-1]  # (batch_size, hidden_dim)

        logits = self.fc(last_hidden)  # (batch_size, output_dim)
        return logits

    def training_step(self, batch, _):
        x, y = batch
        logits = self(x)
        loss = self.loss_fn(logits, y)

        preds = torch.argmax(logits, dim=1)
        acc = self.train_accuracy(preds, y)

        self.log("train_loss", loss, prog_bar=True)
        self.log("train_acc", acc, prog_bar=True)
        return loss

    def validation_step(self, batch, _):
        x, y = batch
        logits = self(x)
        loss = self.loss_fn(logits, y)

        preds = torch.argmax(logits, dim=1)
        acc = self.val_accuracy(preds, y)

        self.log("val_loss", loss, prog_bar=True)
        self.log("val_acc", acc, prog_bar=True)
        return loss

    def configure_optimizers(self):
        return Adam(self.parameters(), lr=0.001)

    def train_dataloader(self):
        return train_loader

    def val_dataloader(self):
        return test_loader


# 모델 생성
print("\n[모델 생성 중...]")
model = IMDBLSTMModel(
    vocab_size=vocab_size,
    embedding_dim=embedding_dim,
    hidden_dim=hidden_dim,
    output_dim=output_dim
)

# Trainer 생성
print("[학습 시작...]")
trainer = pl.Trainer(
    accelerator="gpu" if torch.cuda.is_available() else "cpu",
    devices=1,
    max_epochs=num_epochs,
    enable_progress_bar=True,
    enable_model_summary=True
)

# 모델 학습
trainer.fit(model)

print("\n[학습 완료!]")
