"""MNIST 숫자 조건부 GAN의 생성자와 판별자를 정의합니다."""

# 텐서 연산을 위해 torch를 가져옵니다.
import torch
# 신경망 계층을 사용하기 위해 torch.nn을 nn으로 가져옵니다.
from torch import nn


# 숫자 레이블을 조건으로 이미지를 생성하는 모델을 정의합니다.
class ConditionalGenerator(nn.Module):
    """잠재 벡터와 숫자 레이블로 28×28 흑백 이미지를 생성합니다."""

    def __init__(self, latent_dim: int = 100, class_count: int = 10) -> None:
        # 부모 클래스의 초기화 메서드를 호출합니다.
        super().__init__()
        # 숫자 레이블을 잠재 벡터와 같은 크기의 임베딩으로 변환합니다.
        self.label_embedding = nn.Embedding(class_count, latent_dim)
        # 잠재 벡터와 레이블 임베딩을 결합하여 이미지 벡터를 생성합니다.
        self.network = nn.Sequential(
            # 결합 입력을 256차원 특징으로 변환합니다.
            nn.Linear(latent_dim * 2, 256),
            # 음수 입력에도 작은 기울기를 유지합니다.
            nn.LeakyReLU(0.2, inplace=True),
            # 특징 차원을 512로 확장합니다.
            nn.Linear(256, 512),
            # 배치 단위 정규화로 학습을 안정화합니다.
            nn.BatchNorm1d(512),
            # 비선형성을 추가합니다.
            nn.LeakyReLU(0.2, inplace=True),
            # 특징 차원을 1024로 확장합니다.
            nn.Linear(512, 1024),
            # 확장 특징을 정규화합니다.
            nn.BatchNorm1d(1024),
            # 출력 계층 전 활성화 함수를 적용합니다.
            nn.LeakyReLU(0.2, inplace=True),
            # 28×28 픽셀 수인 784차원으로 변환합니다.
            nn.Linear(1024, 28 * 28),
            # 픽셀값을 -1과 1 사이로 제한합니다.
            nn.Tanh(),
        )

    def forward(self, noise: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        # 숫자 레이블을 임베딩 벡터로 변환합니다.
        embedded_labels = self.label_embedding(labels)
        # 잠재 벡터와 레이블 임베딩을 연결합니다.
        combined_input = torch.cat((noise, embedded_labels), dim=1)
        # 결합 입력으로 가짜 이미지 벡터를 생성하여 반환합니다.
        return self.network(combined_input)


# 이미지와 숫자 조건이 실제 데이터와 일치하는지 판별하는 모델을 정의합니다.
class ConditionalDiscriminator(nn.Module):
    """이미지가 주어진 숫자 조건에 맞는 실제 이미지인지 판별합니다."""

    def __init__(self, class_count: int = 10) -> None:
        # 부모 클래스의 초기화 메서드를 호출합니다.
        super().__init__()
        # 숫자 레이블을 이미지 크기와 같은 784차원으로 임베딩합니다.
        self.label_embedding = nn.Embedding(class_count, 28 * 28)
        # 이미지와 레이블 임베딩을 결합해 실제 여부 로짓을 계산합니다.
        self.network = nn.Sequential(
            # 결합된 1568차원 입력을 512차원으로 줄입니다.
            nn.Linear(28 * 28 * 2, 512),
            # 판별자에 비선형성을 추가합니다.
            nn.LeakyReLU(0.2, inplace=True),
            # 일부 뉴런을 비활성화하여 과적합을 줄입니다.
            nn.Dropout(0.3),
            # 특징을 256차원으로 줄입니다.
            nn.Linear(512, 256),
            # 두 번째 비선형 활성화를 적용합니다.
            nn.LeakyReLU(0.2, inplace=True),
            # 추가 Dropout을 적용합니다.
            nn.Dropout(0.3),
            # 실제 여부를 나타내는 하나의 로짓을 출력합니다.
            nn.Linear(256, 1),
        )

    def forward(self, images: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        # 숫자 레이블을 이미지 크기의 벡터로 변환합니다.
        embedded_labels = self.label_embedding(labels)
        # 이미지와 조건 벡터를 연결합니다.
        combined_input = torch.cat((images, embedded_labels), dim=1)
        # 결합 입력의 실제 여부 로짓을 반환합니다.
        return self.network(combined_input)


# Linear 및 Embedding 계층의 초기 가중치를 설정하는 함수를 정의합니다.
def initialize_weights(module: nn.Module) -> None:
    """GAN 계층의 가중치를 작은 정규분포 값으로 초기화합니다."""
    # Linear 계층인지 확인합니다.
    if isinstance(module, nn.Linear):
        # 가중치를 평균 0, 표준편차 0.02로 초기화합니다.
        nn.init.normal_(module.weight.data, 0.0, 0.02)
        # 편향이 존재하는 경우인지 확인합니다.
        if module.bias is not None:
            # 편향을 0으로 초기화합니다.
            nn.init.constant_(module.bias.data, 0.0)
    # Embedding 계층인지 확인합니다.
    elif isinstance(module, nn.Embedding):
        # 임베딩 가중치를 작은 정규분포 값으로 초기화합니다.
        nn.init.normal_(module.weight.data, 0.0, 0.02)
