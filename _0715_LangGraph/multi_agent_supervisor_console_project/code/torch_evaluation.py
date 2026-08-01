# -*- coding: utf-8 -*-
"""PyTorch 텐서로 라우터 정확도와 비용 지표를 계산하는 평가 모듈입니다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import torch

# 규칙 라우터 함수를 가져옵니다.
from router import route_rule

# 정답 라벨이 포함된 라우팅 테스트 데이터입니다.
TESTSET: tuple[tuple[str, str], ...] = (
    ("환불은 며칠 안에 신청해야 해?", "policy"),
    ("무료배송 기준이 어떻게 돼?", "policy"),
    ("포인트 적립은 언제 돼?", "policy"),
    ("교환하려면 어떻게 해?", "policy"),
    ("전자기기 추천 좀 해줘", "sales"),
    ("패션 인기상품 뭐 있어?", "sales"),
    ("선물용으로 좋은 거 골라줘", "sales"),
    ("가성비 좋은 거 없을까?", "sales"),
    ("주문한 거 무를 수 있어?", "policy"),
    ("이거 며칠이면 받아볼 수 있어?", "policy"),
)

# 문자열 라벨을 텐서 정수로 바꾸기 위한 매핑입니다.
LABEL_TO_INDEX: dict[str, int] = {"sales": 0, "policy": 1}


@dataclass(frozen=True)
class EvaluationResult:
    """라우터 평가 결과를 구조적으로 보관합니다."""

    name: str
    accuracy: float
    correct: int
    total: int
    llm_calls: int
    predictions: tuple[str, ...]


def evaluate_rule_router() -> EvaluationResult:
    """규칙 라우터를 테스트셋에 적용하고 PyTorch로 정확도를 계산합니다."""
    # 모델 예측 라벨을 저장할 빈 리스트를 생성합니다.
    predictions: list[str] = []

    # 테스트 질문을 하나씩 규칙 라우터에 전달합니다.
    for question, _gold in TESTSET:
        # 규칙 라우터의 결정을 얻습니다.
        decision = route_rule(question)

        # HTML 예제와 동일하게 애매한 질문은 sales를 기본값으로 사용합니다.
        predicted = decision.target if decision.target != "unknown" else "sales"

        # 평가를 위해 예측 라벨을 목록에 추가합니다.
        predictions.append(predicted)

    # 정답 라벨을 정수 인덱스 텐서로 변환합니다.
    gold_tensor = torch.tensor(
        [LABEL_TO_INDEX[gold] for _question, gold in TESTSET],
        dtype=torch.long,
    )

    # 예측 라벨을 정수 인덱스 텐서로 변환합니다.
    prediction_tensor = torch.tensor(
        [LABEL_TO_INDEX[prediction] for prediction in predictions],
        dtype=torch.long,
    )

    # 각 위치에서 예측과 정답이 같은지 나타내는 불리언 텐서를 생성합니다.
    correct_tensor = prediction_tensor.eq(gold_tensor)

    # True의 개수를 합산하여 맞힌 질문 수를 계산합니다.
    correct = int(correct_tensor.sum().item())

    # 불리언 텐서를 float로 바꾼 뒤 평균을 구해 정확도를 계산합니다.
    accuracy = float(correct_tensor.float().mean().item())

    # 구조화된 평가 결과를 반환합니다.
    return EvaluationResult(
        name="규칙 라우터",
        accuracy=accuracy,
        correct=correct,
        total=len(TESTSET),
        llm_calls=0,
        predictions=tuple(predictions),
    )


def evaluate_predictions(
    *,
    name: str,
    predictions: list[str],
    llm_calls: int,
) -> EvaluationResult:
    """외부에서 얻은 LLM/하이브리드 예측 목록을 PyTorch 텐서로 평가합니다."""
    # 예측 개수가 테스트셋 크기와 같은지 검사합니다.
    if len(predictions) != len(TESTSET):
        raise ValueError("예측 개수와 테스트셋 크기가 일치하지 않습니다.")

    # 정답 문자열을 정수 텐서로 변환합니다.
    gold_tensor = torch.tensor(
        [LABEL_TO_INDEX[gold] for _question, gold in TESTSET],
        dtype=torch.long,
    )

    # 예측 문자열을 정수 텐서로 변환합니다.
    prediction_tensor = torch.tensor(
        [LABEL_TO_INDEX[prediction] for prediction in predictions],
        dtype=torch.long,
    )

    # 정답과 예측의 위치별 일치 여부를 계산합니다.
    correct_tensor = prediction_tensor.eq(gold_tensor)

    # 일치한 항목 개수를 Python 정수로 변환합니다.
    correct = int(correct_tensor.sum().item())

    # 전체 평균으로 정확도를 계산합니다.
    accuracy = float(correct_tensor.float().mean().item())

    # 계산한 결과를 EvaluationResult 객체로 반환합니다.
    return EvaluationResult(
        name=name,
        accuracy=accuracy,
        correct=correct,
        total=len(TESTSET),
        llm_calls=llm_calls,
        predictions=tuple(predictions),
    )
