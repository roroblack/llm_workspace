"""
GAN을 구성하는 생성자와 판별자 신경망을 정의하는 모듈입니다.
"""

# 신경망 모델과 계층을 사용하기 위해 PyTorch 패키지를 가져옵니다.
import torch

# nn.Module과 다양한 신경망 계층을 사용하기 위해 torch.nn을 nn이라는 이름으로 가져옵니다.
from torch import nn


# 생성자 신경망을 정의하기 위해 nn.Module을 상속합니다.
class Generator(nn.Module):
    """무작위 잠재 벡터를 입력받아 28×28 크기의 가짜 MNIST 이미지를 생성합니다."""

    # 생성자 모델을 초기화하는 메서드를 정의합니다.
    def __init__(self, latent_dim: int, image_size: int) -> None:
        # nn.Module의 초기화 로직을 실행합니다.
        super().__init__()

        # 여러 신경망 계층을 순서대로 실행하도록 Sequential 모델을 생성합니다.
        self.network = nn.Sequential(
            # 잠재 벡터를 256차원 특징 벡터로 변환하는 완전연결 계층입니다.
            nn.Linear(latent_dim, 256),

            # 음수 영역에도 작은 기울기를 유지하여 학습 정체를 줄입니다.
            nn.LeakyReLU(negative_slope=0.2, inplace=True),

            # 256차원 특징을 512차원으로 확장합니다.
            nn.Linear(256, 512),

            # 중간 특징값을 정규화하여 학습을 안정화합니다.
            nn.BatchNorm1d(512),

            # 비선형 표현 능력을 높이기 위해 LeakyReLU를 적용합니다.
            nn.LeakyReLU(negative_slope=0.2, inplace=True),

            # 512차원 특징을 1024차원으로 확장합니다.
            nn.Linear(512, 1024),

            # 1024차원 특징값을 배치 단위로 정규화합니다.
            nn.BatchNorm1d(1024),

            # 마지막 출력 계층 전에도 비선형 활성화 함수를 적용합니다.
            nn.LeakyReLU(negative_slope=0.2, inplace=True),

            # 1024차원 특징을 이미지 전체 픽셀 수로 변환합니다.
            nn.Linear(1024, image_size),

            # 출력 픽셀값을 -1과 1 사이로 제한합니다.
            nn.Tanh(),
        )

    # 입력 잠재 벡터가 모델을 통과하는 순전파 과정을 정의합니다.
    def forward(self, noise: torch.Tensor) -> torch.Tensor:
        # 잠재 벡터를 생성자 네트워크에 전달하여 평탄화된 가짜 이미지를 생성합니다.
        generated_image = self.network(noise)

        # 생성된 평탄화 이미지를 호출한 코드에 반환합니다.
        return generated_image


# 판별자 신경망을 정의하기 위해 nn.Module을 상속합니다.
class Discriminator(nn.Module):
    """입력 이미지가 실제 이미지인지 생성자가 만든 가짜 이미지인지 판별합니다."""

    # 판별자 모델을 초기화하는 메서드를 정의합니다.
    def __init__(self, image_size: int) -> None:
        # nn.Module의 초기화 로직을 실행합니다.
        super().__init__()

        # 입력 이미지가 실제일 확률을 계산하는 순차 신경망을 생성합니다.
        self.network = nn.Sequential(
            # 이미지 픽셀 벡터를 512차원 특징으로 변환합니다.
            nn.Linear(image_size, 512),

            # 음수 입력에서도 작은 기울기를 유지하는 활성화 함수를 적용합니다.
            nn.LeakyReLU(negative_slope=0.2, inplace=True),

            # 일부 뉴런을 무작위로 비활성화하여 과적합을 줄입니다.
            nn.Dropout(p=0.3),

            # 512차원 특징을 256차원으로 축소합니다.
            nn.Linear(512, 256),

            # 판별자에 필요한 비선형성을 추가합니다.
            nn.LeakyReLU(negative_slope=0.2, inplace=True),

            # 판별자가 특정 픽셀 조합에 지나치게 의존하지 않도록 Dropout을 적용합니다.
            nn.Dropout(p=0.3),

            # 256차원 특징을 실제/가짜 판별을 위한 하나의 로짓값으로 변환합니다.
            nn.Linear(256, 1),
        )

    # 입력 이미지가 판별자 모델을 통과하는 순전파 과정을 정의합니다.
    def forward(self, image: torch.Tensor) -> torch.Tensor:
        # 입력 이미지를 판별자 네트워크에 전달하여 실제 이미지에 대한 로짓값을 계산합니다.
        logits = self.network(image)

        # 수치적으로 안정적인 BCEWithLogitsLoss를 사용하기 위해 Sigmoid 전 로짓을 반환합니다.
        return logits


# GAN 학습 초기에 사용할 가중치 초기화 함수를 정의합니다.
def initialize_weights(module: nn.Module) -> None:
    """Linear 계층의 가중치를 정규분포로 초기화하고 편향을 0으로 설정합니다."""

    # 현재 모듈이 완전연결 계층인지 확인합니다.
    if isinstance(module, nn.Linear):
        # 완전연결 계층의 가중치를 평균 0, 표준편차 0.02인 정규분포로 초기화합니다.
        nn.init.normal_(module.weight.data, mean=0.0, std=0.02)

        # 현재 계층에 편향이 정의되어 있는지 확인합니다.
        if module.bias is not None:
            # 편향값을 모두 0으로 초기화합니다.
            nn.init.constant_(module.bias.data, 0.0)
