# -*- coding: utf-8 -*-
"""PyTorch 텐서를 사용하여 규칙 기반 우선순위 점수 계산 원리를 확인합니다."""

# 텐서 생성과 행렬 연산을 위해 PyTorch를 가져옵니다.
import torch


# 세 개의 특징을 긴급도 점수로 합산할 때 사용할 가중치를 정의합니다.
FEATURE_WEIGHTS = torch.tensor([3.0, 2.0, 1.0], dtype=torch.float32)


def text_to_feature_tensor(text: str) -> torch.Tensor:
    """티켓 문장을 결제·오류·환불 특징을 나타내는 0/1 텐서로 변환합니다."""

    # 결제 관련 단어가 포함되면 1.0, 없으면 0.0으로 변환합니다.
    payment_feature = 1.0 if "결제" in text else 0.0

    # 오류 또는 작동 실패 표현이 포함되면 1.0, 없으면 0.0으로 변환합니다.
    error_feature = 1.0 if any(word in text for word in ["오류", "안 돼", "안돼", "먹통"]) else 0.0

    # 환불 또는 교환 표현이 포함되면 1.0, 없으면 0.0으로 변환합니다.
    refund_feature = 1.0 if any(word in text for word in ["환불", "교환"]) else 0.0

    # 세 특징을 float32 자료형의 1차원 텐서로 묶어 반환합니다.
    return torch.tensor(
        [payment_feature, error_feature, refund_feature],
        dtype=torch.float32,
    )


def calculate_priority_score(text: str) -> tuple[torch.Tensor, float, str]:
    """특징 텐서와 가중치의 내적으로 점수를 계산하고 우선순위 문자열을 반환합니다."""

    # 입력 문장을 세 개의 이진 특징값을 가진 텐서로 변환합니다.
    features = text_to_feature_tensor(text)

    # 특징 텐서와 가중치 텐서의 내적을 계산하여 하나의 점수를 만듭니다.
    score_tensor = torch.dot(features, FEATURE_WEIGHTS)

    # 출력과 조건 비교에 사용하기 쉽도록 0차원 텐서를 파이썬 float로 변환합니다.
    score = float(score_tensor.item())

    # 점수가 3 이상이면 긴급으로 판정합니다.
    if score >= 3.0:
        priority = "긴급"
    # 점수가 1 이상 3 미만이면 높음으로 판정합니다.
    elif score >= 1.0:
        priority = "높음"
    # 특징이 하나도 없으면 보통으로 판정합니다.
    else:
        priority = "보통"

    # 특징 텐서, 숫자 점수, 최종 우선순위를 함께 반환합니다.
    return features, score, priority


def run_torch_demo() -> None:
    """콘솔에서 티켓 문장을 입력받아 PyTorch 기반 점수 계산 과정을 출력합니다."""

    # 현재 설치된 PyTorch 버전을 출력합니다.
    print(f"PyTorch 버전: {torch.__version__}")

    # CUDA 사용 가능 여부를 확인하여 현재 실행 장치를 안내합니다.
    print(f"CUDA 사용 가능: {torch.cuda.is_available()}")

    # 사용자가 분석할 티켓 문장을 입력하도록 요청합니다.
    text = input("티켓 내용을 입력하세요: ").strip()

    # 빈 입력이면 이해하기 쉬운 기본 예제를 사용합니다.
    if not text:
        text = "결제가 안 돼요. 오류가 계속 발생합니다."

    # 텐서 특징, 점수, 우선순위를 계산합니다.
    features, score, priority = calculate_priority_score(text)

    # 각 특징의 순서를 사용자가 이해할 수 있도록 출력합니다.
    print("특징 순서       : [결제, 오류/작동실패, 환불/교환]")

    # 실제 생성된 특징 텐서를 출력합니다.
    print("특징 텐서       :", features)

    # 가중치 텐서를 출력합니다.
    print("가중치 텐서     :", FEATURE_WEIGHTS)

    # 내적으로 얻은 숫자 점수를 출력합니다.
    print("긴급도 점수     :", score)

    # 점수 구간에 따라 결정된 최종 우선순위를 출력합니다.
    print("판정 우선순위   :", priority)
