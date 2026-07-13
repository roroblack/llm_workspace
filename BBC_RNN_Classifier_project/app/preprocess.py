"""텍스트 정제, 토큰화, 패딩, 라벨 인코딩을 담당하는 모듈."""

from __future__ import annotations

import re
from collections import Counter
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np


STOP_WORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with", "after", "as", "by", "at", "during",
}


def clean_text(text: str, remove_stopwords: bool = True) -> str:
    """영문 기사 문장에서 특수문자와 불필요한 단어를 제거한다."""

    text = text.lower()                                      # 대문자와 소문자를 같은 단어로 처리하기 위해 소문자로 변환한다.
    text = re.sub(r"[^a-z\s]", " ", text)                  # 알파벳과 공백을 제외한 문장부호와 숫자를 공백으로 바꾼다.
    tokens = text.split()                                    # 공백 기준으로 단어를 분리한다.
    if remove_stopwords:                                     # 제외어 제거 옵션이 켜져 있는지 확인한다.
        tokens = [w for w in tokens if w not in STOP_WORDS]  # 의미가 약한 불용어를 제거한다.
    return " ".join(tokens)                                  # 정제된 토큰들을 다시 하나의 문자열로 합친다.


def build_vocab(texts: Sequence[str], max_vocab: int) -> Dict[str, int]:
    """학습 데이터에서 자주 등장한 단어를 정수 인덱스로 매핑하는 사전을 만든다."""

    counter: Counter[str] = Counter()                        # 단어 빈도를 계산하기 위한 Counter 객체를 만든다.
    for text in texts:                                       # 모든 기사 문장을 하나씩 순회한다.
        counter.update(text.split())                         # 문장의 단어 빈도를 Counter에 누적한다.
    most_common = counter.most_common(max_vocab - 2)          # PAD와 OOV 토큰 자리를 제외하고 상위 단어를 선택한다.
    vocab = {"<PAD>": 0, "<OOV>": 1}                        # 0은 패딩, 1은 사전에 없는 단어를 의미하도록 예약한다.
    for index, (word, _) in enumerate(most_common, start=2):  # 실제 단어 인덱스는 2부터 시작한다.
        vocab[word] = index                                  # 단어를 정수 인덱스에 매핑한다.
    return vocab                                             # 완성된 단어 사전을 반환한다.


def texts_to_sequences(texts: Sequence[str], vocab: Dict[str, int]) -> List[List[int]]:
    """문장 목록을 정수 토큰 시퀀스 목록으로 변환한다."""

    sequences: List[List[int]] = []                          # 변환 결과를 저장할 리스트를 준비한다.
    for text in texts:                                       # 각 문장을 순회한다.
        seq = [vocab.get(word, vocab["<OOV>"]) for word in text.split()]  # 단어를 정수로 바꾸고 미등록 단어는 OOV로 처리한다.
        sequences.append(seq)                                # 변환된 정수 시퀀스를 결과 리스트에 추가한다.
    return sequences                                         # 전체 정수 시퀀스 목록을 반환한다.


def pad_sequences(sequences: Sequence[Sequence[int]], max_len: int) -> np.ndarray:
    """서로 다른 길이의 정수 시퀀스를 동일한 길이의 2차원 배열로 맞춘다."""

    padded = np.zeros((len(sequences), max_len), dtype=np.int64)  # 모든 값을 0으로 채운 패딩 배열을 먼저 만든다.
    for i, seq in enumerate(sequences):                           # 각 시퀀스와 해당 위치를 함께 순회한다.
        truncated = list(seq)[-max_len:]                          # max_len보다 긴 문장은 뒤쪽 기준으로 자른다.
        padded[i, -len(truncated):] = truncated if truncated else []  # 짧은 문장은 앞쪽을 0으로 남기고 뒤쪽에 토큰을 채운다.
    return padded                                                   # 패딩이 끝난 2차원 배열을 반환한다.


def encode_labels(labels: Sequence[str]) -> Tuple[np.ndarray, Dict[str, int], Dict[int, str]]:
    """문자열 라벨을 정수 라벨로 변환하고 양방향 라벨 사전을 반환한다."""

    label_to_id = {label: idx for idx, label in enumerate(sorted(set(labels)))}  # 라벨명을 정수 ID로 매핑한다.
    id_to_label = {idx: label for label, idx in label_to_id.items()}             # 예측 결과 해석을 위해 정수 ID를 라벨명으로 되돌리는 사전을 만든다.
    encoded = np.array([label_to_id[label] for label in labels], dtype=np.int64) # 각 정답 라벨을 정수로 변환한다.
    return encoded, label_to_id, id_to_label                                     # 인코딩 결과와 라벨 사전들을 반환한다.
