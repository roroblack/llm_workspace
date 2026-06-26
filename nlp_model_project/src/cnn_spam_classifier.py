# ./src/cnn_spam_classifier.py

'''
pythorch 기반 스팸 메일 분류기 작성 스크립트 파일
SMS 문장을 숫자 시퀀스
Embedding + Cov1D + MaxPooling + Linear + Softmax 구조로 정상/스팸 분류 모델
'''

import os
import random

# 인터넷에서 csv 받으려고 씀
import urllib.request

# 단어 빈도수 쉽게 계산
from collections import Counter

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

# ----------------------------------------------------



# 난수 시드 고정 함수 정의
def set_seed(seed:int = 42):
    random.seed(seed)
    np.random.seed(seed)

    # CPU 사용시 PyTorch 난수 시드 고정
    torch.manual_seed(seed)

    # GPU 사용시 PyTorch 난수 시드 고정
    # torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    # torch.backends.cudnn.deterministic = True
    # torch.backends.cudnn.benchmark = False
    # return
#----------------------------------------------------



# 간단한 영어 토큰화 수행하는 함수 정의
def simple_tokenize(text:str) -> list[str]:
    # 전달받은 문장을 문자열로 변환한 뒤에 소문자로 변환
    text = str(text).lower()

    # 문장을 공백 기준으로 분리하여 단어 토큰 리스트 생성
    tokens = text.split()
    return tokens
#----------------------------------------------------



# 훈련 데이터에 대한 단어 사전 만드는 함수 정의
def build_vocab(texts:pd.Series, min_freq:int = 1) -> tuple[dict[str, int], Counter] :
    # 단어 빈도수 계산
    counter = Counter()
    for text in texts:
        tokens = simple_tokenize(text)
        counter.update(tokens)


    # 최소 빈도수 이상인 단어만 단어 사전에 추가
    vocab = {word: idx + 2 for idx, (word, freq) in enumerate(counter.items()) if freq >= min_freq}

    # 특수 토큰 추가
    # 0번 인덱스는 패딩 토큰, 1번 인덱스는 미등록 (알 수 없는) 단어 토큰으로 예약
    # word2idx = {'<PAD>': 0, '<UNK>': 1}
    vocab['<PAD>'] = 0  # 패딩 토큰
    vocab['<UNK>'] = 1  # 미등록 (알 수 없는) 단어 토큰

    # 빈도수 높은 단어부터 정렬해 단어 사전에 추가
    for word, freq in counter.most_common():
        # min_freq 이상 등장한 단어만 단어 사전에 추가
        if freq >= min_freq:
            # 아직 사전에 없는 단어면 새로운 번호를 부여
            if word not in vocab:
                vocab[word] = len(vocab)
    # for --------------------------------------------------

    # 단어-번호 사전과 단어 빈도 수 Counter 객체 반환
    return vocab, counter
# ----------------------------------------------------



def encode_and_pad(text:str, word2idx:dict[str, int], max_len:int) -> list[int]:
    # 문장을 토큰화
    tokens = simple_tokenize(text)

    # 토큰을 단어 번호로 변환
    encoded = [word2idx.get(token, word2idx['<UNK>']) for token in tokens]

    # 문장이 max_len 보다 길면 앞에 max_len 위치까지 자름
    # 문장이 max_len 보다 짧으면 뒤쪽에 <PAD> 번호 0 을 추가해서 길이를 맞춤
    # 패딩 수행
    if len(encoded) < max_len:
        # 패딩 토큰으로 채움
        encoded += [word2idx['<PAD>']] * (max_len - len(encoded))
    else:
        # max_len보다 길면 자름
        encoded = encoded[:max_len]

    # 또 다른 슬라이싱 스타일
    # encoded = encoded[:max_len] + [word2idx['<PAD>']] * (max_len - len(encoded[:max_len]))
    
    return encoded
# ----------------------------------------------------

# SMS 문장과 레이블 (ham | spam) 을 Torch DataLoader 가 읽을 수 있도록 구성하는 Dataset 클래스 정의
class SMSDataset(Dataset):

    # 생성자가 해당 클래스 객체 생성시, 문장, 레이블, 단어 사전, 최대 길이를 전달받도록 함
    def __init__(self, texts:pd.Series, labels:pd.Series, word2idx:dict[str, int], max_len:int):

        self.texts          = list(texts)               # SMS 문장들을 리스트로 변환하여 저장
        self.labels         = list(labels.astype(int))  # 레이블을 정수형으로 변환
        self.word2idx       = word2idx                  # 정수 번호로 바꾸기 위한 사전 저장
        self.max_len        = max_len                   # 모든 문장 맟출 최대 길이 저장

    def __len__(self) -> int:
        return len(self.texts)
    
    def __getitem__(self, idx:int) -> tuple[torch.Tensor, torch.Tensor]:
        # idx 번째 문장과 레이블을 가져옴
        text = self.texts[idx]
        # idx 위치의 정답 레이블도 꺼냄
        label = self.labels[idx]

        # 문장을 정수 시퀀스로 변환하고 패딩 수행
        encoded_text = encode_and_pad(text, self.word2idx, self.max_len)    # X

        # 정수 시퀀스를 Torch Tensor 로 변환
        # 정답은 float 으로 처리 (이진 분류 문제이므로)
        text_tensor = torch.tensor(encoded_text, dtype=torch.long)          # X tensor
        label_tensor = torch.tensor(label, dtype=torch.float32)             # y tensor

        # 입력 텐서와 정답 텐서를 반환 함
        return text_tensor, label_tensor
    
# 모델 설계
# Embedding + Conv1D + MaxPooling + Linear + Softmax 구조 의 CNN 문장 분류 모델
class TextCNN(nn.Module):
    def __init__(self, 
                 vocab_size:int, 
                 embedding_dim:int = 32, 
                 num_filters:int = 32, 
                 kernel_size:int = 5,
                 dropout_ratio:float | int = 0.3,
                 output_dim:int = 1
                 ):
        # 부모 생성자 호출 (후손 생성자 첫줄에만 기입 가능)
        super().__init__()

        # 신경망 계층에 대한 설정 선언
        # 1. Embedding 레이어: 단어 번호를 임베딩 벡터로 변환
        self.embedding = nn.Embedding(
            num_embeddings = vocab_size, 
            embedding_dim = embedding_dim,
            padding_idx = 0                                 # 패딩 토큰 인덱스 지정
            )

        # 2. Dropout 레이어: 과적합 방지
        self.dropout = nn.Dropout(dropout_ratio)            # 기본값 0.3 이라 뉴런 수 30 퍼 줄임

        # 3. Conv1D 레이어: 문장 내 단어 시퀀스에 대한 합성곱 연산 수행
        # Conv1D 레이어 정의
        self.convs = nn.ModuleList([
            nn.Conv1d(in_channels=embedding_dim, out_channels=num_filters, kernel_size=kernel_size)
            for _ in range(len(filter_sizes))
        ])

        # MaxPooling 레이어 정의
        self.pool = nn.AdaptiveMaxPool1d(1)

        # 출력 레이어 정의
        self.fc = nn.Linear(num_filters * len(filter_sizes), output_dim)

    def forward(self, x):
        # 입력 x의 shape: (batch_size, max_len)
        embedded = self.embedding(x)  # shape: (batch_size, max_len, embedding_dim)
        embedded = embedded.permute(0, 2, 1)  # shape: (batch_size, embedding_dim, max_len)

        # Conv1D + ReLU + MaxPooling 수행
        conv_outputs = [self.pool(torch.relu(conv(embedded))).squeeze(2) for conv in self.convs]
        
        # 모든 Conv1D 결과를 연결
        cat = torch.cat(conv_outputs, dim=1)  # shape: (batch_size, num_filters * len(filter_sizes))

        # Dropout 적용
        dropped = self.dropout(cat)

        # 최종 출력 레이어 통과
        output = self.fc(dropped)  # shape: (batch_size, output_dim)
        
        return output