# -*- coding: utf-8 -*-
"""벡터 계산에 공통으로 사용하는 PyTorch 유틸리티 모듈입니다."""

from __future__ import annotations

from typing import Iterable

import torch


def to_tensor(values: Iterable[float]) -> torch.Tensor:
    """숫자 반복 객체를 float32 형식의 1차원 PyTorch 텐서로 변환합니다."""
    return torch.tensor(list(values), dtype=torch.float32)


def cosine_similarity(a: Iterable[float], b: Iterable[float]) -> float:
    """두 벡터의 코사인 유사도를 계산하여 파이썬 float 값으로 반환합니다."""
    # 첫 번째 입력 벡터를 PyTorch 텐서로 변환합니다.
    tensor_a = to_tensor(a)
    # 두 번째 입력 벡터를 PyTorch 텐서로 변환합니다.
    tensor_b = to_tensor(b)
    # 벡터 길이가 다르면 내적을 계산할 수 없으므로 명확한 오류를 발생시킵니다.
    if tensor_a.numel() != tensor_b.numel():
        raise ValueError("두 벡터의 차원이 서로 다릅니다.")
    # 영벡터가 포함되면 0으로 나누는 문제가 생기므로 유사도 0.0을 반환합니다.
    if torch.linalg.vector_norm(tensor_a) == 0 or torch.linalg.vector_norm(tensor_b) == 0:
        return 0.0
    # torch.nn.functional.cosine_similarity를 사용해 두 벡터의 방향 유사도를 계산합니다.
    score = torch.nn.functional.cosine_similarity(
        tensor_a.unsqueeze(0), tensor_b.unsqueeze(0), dim=1
    )
    # 단일 원소 텐서를 일반 float 값으로 변환해 반환합니다.
    return float(score.item())


def top_k_indices(query_vector: Iterable[float], document_vectors: list[list[float]], k: int = 3) -> list[tuple[int, float]]:
    """질문 벡터와 가장 유사한 문서 벡터의 인덱스와 점수를 상위 k개 반환합니다."""
    # 질문 벡터를 1행짜리 텐서로 변환합니다.
    query = to_tensor(query_vector).unsqueeze(0)
    # 문서 벡터 목록을 2차원 텐서로 변환합니다.
    documents = torch.tensor(document_vectors, dtype=torch.float32)
    # 문서 벡터가 비어 있으면 검색 결과도 빈 목록으로 반환합니다.
    if documents.numel() == 0:
        return []
    # 모든 문서 벡터를 행 단위로 정규화합니다.
    documents = torch.nn.functional.normalize(documents, p=2, dim=1)
    # 질문 벡터를 행 단위로 정규화합니다.
    query = torch.nn.functional.normalize(query, p=2, dim=1)
    # 정규화된 벡터끼리 행렬 곱을 수행하면 코사인 유사도가 계산됩니다.
    scores = torch.matmul(documents, query.transpose(0, 1)).squeeze(1)
    # 요청한 k가 문서 수보다 크지 않도록 실제 반환 개수를 제한합니다.
    actual_k = min(max(k, 1), scores.numel())
    # 가장 높은 점수와 해당 인덱스를 구합니다.
    values, indices = torch.topk(scores, k=actual_k)
    # 텐서 결과를 사용하기 편한 (인덱스, 점수) 튜플 목록으로 변환합니다.
    return [(int(index.item()), float(value.item())) for index, value in zip(indices, values)]
