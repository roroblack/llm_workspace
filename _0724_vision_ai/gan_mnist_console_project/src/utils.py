"""
난수 고정, 이미지 저장, 손실 그래프 저장, 체크포인트 처리 기능을 제공합니다.
"""

# Python 내장 난수 생성기의 시드를 고정하기 위해 random 모듈을 가져옵니다.
import random

# 경로 객체를 사용하기 위해 pathlib의 Path 클래스를 가져옵니다.
from pathlib import Path

# 수치 연산과 NumPy 난수 시드를 고정하기 위해 numpy를 가져옵니다.
import numpy as np

# 손실 그래프를 이미지 파일로 저장하기 위해 matplotlib.pyplot을 가져옵니다.
import matplotlib.pyplot as plt

# 텐서 저장, 로드, 난수 생성 기능을 사용하기 위해 torch를 가져옵니다.
import torch

# 여러 장의 텐서를 격자 이미지로 저장하기 위해 torchvision.utils의 save_image를 가져옵니다.
from torchvision.utils import save_image


# 실행 결과의 재현성을 높이기 위한 시드 고정 함수를 정의합니다.
def set_random_seed(seed: int) -> None:
    """Python, NumPy, PyTorch의 난수 시드를 동일한 값으로 고정합니다."""

    # Python 표준 난수 생성기의 시드를 고정합니다.
    random.seed(seed)

    # NumPy 난수 생성기의 시드를 고정합니다.
    np.random.seed(seed)

    # CPU에서 사용하는 PyTorch 난수 생성기의 시드를 고정합니다.
    torch.manual_seed(seed)

    # 사용 가능한 모든 CUDA GPU의 난수 생성기 시드를 고정합니다.
    torch.cuda.manual_seed_all(seed)

    # 동일 입력에 대해 가능한 한 같은 알고리즘을 사용하도록 설정합니다.
    torch.backends.cudnn.deterministic = True

    # 실행 속도를 위해 알고리즘을 자동 탐색하는 기능을 비활성화합니다.
    torch.backends.cudnn.benchmark = False


# 생성자가 만든 평탄화 이미지 텐서를 PNG 파일로 저장하는 함수를 정의합니다.
def save_generated_images(
    generated_images: torch.Tensor,
    output_path: Path,
    image_channels: int,
    image_height: int,
    image_width: int,
) -> None:
    """생성 이미지 텐서를 원래 이미지 모양으로 복원하여 격자 PNG로 저장합니다."""

    # 평탄화된 이미지 벡터를 채널, 높이, 너비 형태로 복원합니다.
    restored_images = generated_images.view(
        generated_images.size(0),
        image_channels,
        image_height,
        image_width,
    )

    # Tanh 출력인 -1~1 범위를 저장 가능한 0~1 범위로 변환합니다.
    normalized_images = (restored_images + 1.0) / 2.0

    # 계산 그래프에서 분리하고 CPU 메모리로 이동합니다.
    normalized_images = normalized_images.detach().cpu()

    # 출력 파일의 상위 디렉터리가 없으면 생성합니다.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 여러 이미지를 8열 격자 형태의 PNG 파일로 저장합니다.
    save_image(normalized_images, str(output_path), nrow=8)


# 생성자와 판별자의 손실 변화를 그래프로 저장하는 함수를 정의합니다.
def save_loss_plot(
    generator_losses: list[float],
    discriminator_losses: list[float],
    output_path: Path,
) -> None:
    """에포크별 생성자 및 판별자 평균 손실을 선 그래프로 저장합니다."""

    # 새로운 그래프 객체를 생성하고 가로와 세로 크기를 지정합니다.
    plt.figure(figsize=(10, 6))

    # 생성자 평균 손실값을 선 그래프로 그립니다.
    plt.plot(generator_losses, label="Generator Loss")

    # 판별자 평균 손실값을 선 그래프로 그립니다.
    plt.plot(discriminator_losses, label="Discriminator Loss")

    # 그래프 제목을 지정합니다.
    plt.title("GAN Training Loss")

    # x축이 에포크를 의미하도록 이름을 지정합니다.
    plt.xlabel("Epoch")

    # y축이 손실값을 의미하도록 이름을 지정합니다.
    plt.ylabel("Loss")

    # 두 손실 그래프를 구분할 수 있도록 범례를 표시합니다.
    plt.legend()

    # 값의 변화를 쉽게 읽을 수 있도록 격자선을 표시합니다.
    plt.grid(True)

    # 출력 파일의 상위 디렉터리가 없으면 생성합니다.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 그래프 요소가 잘리지 않도록 여백을 자동 조정합니다.
    plt.tight_layout()

    # 완성된 그래프를 PNG 파일로 저장합니다.
    plt.savefig(output_path)

    # 메모리 누수를 방지하기 위해 현재 그래프를 닫습니다.
    plt.close()


# GAN 학습 상태를 체크포인트 파일로 저장하는 함수를 정의합니다.
def save_checkpoint(
    output_path: Path,
    epoch: int,
    generator: torch.nn.Module,
    discriminator: torch.nn.Module,
    generator_optimizer: torch.optim.Optimizer,
    discriminator_optimizer: torch.optim.Optimizer,
    generator_losses: list[float],
    discriminator_losses: list[float],
) -> None:
    """모델과 옵티마이저 상태 및 손실 기록을 하나의 파일로 저장합니다."""

    # 체크포인트 파일의 상위 디렉터리가 없으면 생성합니다.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 학습을 이어갈 때 필요한 모든 상태값을 딕셔너리로 구성합니다.
    checkpoint = {
        # 마지막으로 완료한 에포크 번호를 저장합니다.
        "epoch": epoch,

        # 생성자의 학습된 파라미터를 저장합니다.
        "generator_state_dict": generator.state_dict(),

        # 판별자의 학습된 파라미터를 저장합니다.
        "discriminator_state_dict": discriminator.state_dict(),

        # 생성자 옵티마이저의 내부 상태를 저장합니다.
        "generator_optimizer_state_dict": generator_optimizer.state_dict(),

        # 판별자 옵티마이저의 내부 상태를 저장합니다.
        "discriminator_optimizer_state_dict": discriminator_optimizer.state_dict(),

        # 지금까지 기록한 생성자 평균 손실 목록을 저장합니다.
        "generator_losses": generator_losses,

        # 지금까지 기록한 판별자 평균 손실 목록을 저장합니다.
        "discriminator_losses": discriminator_losses,
    }

    # 체크포인트 딕셔너리를 PyTorch 바이너리 파일로 저장합니다.
    torch.save(checkpoint, output_path)


# 저장된 체크포인트를 불러오는 함수를 정의합니다.
def load_checkpoint(
    checkpoint_path: Path,
    generator: torch.nn.Module,
    discriminator: torch.nn.Module,
    generator_optimizer: torch.optim.Optimizer | None,
    discriminator_optimizer: torch.optim.Optimizer | None,
    device: torch.device,
) -> tuple[int, list[float], list[float]]:
    """체크포인트를 읽어 모델 상태를 복원하고 다음 에포크 번호를 반환합니다."""

    # 지정한 실행 장치에 맞게 체크포인트 파일을 불러옵니다.
    checkpoint = torch.load(checkpoint_path, map_location=device)

    # 저장된 생성자 파라미터를 현재 생성자 모델에 적용합니다.
    generator.load_state_dict(checkpoint["generator_state_dict"])

    # 저장된 판별자 파라미터를 현재 판별자 모델에 적용합니다.
    discriminator.load_state_dict(checkpoint["discriminator_state_dict"])

    # 생성자 옵티마이저가 전달되었는지 확인합니다.
    if generator_optimizer is not None:
        # 저장된 생성자 옵티마이저 상태를 복원합니다.
        generator_optimizer.load_state_dict(
            checkpoint["generator_optimizer_state_dict"]
        )

    # 판별자 옵티마이저가 전달되었는지 확인합니다.
    if discriminator_optimizer is not None:
        # 저장된 판별자 옵티마이저 상태를 복원합니다.
        discriminator_optimizer.load_state_dict(
            checkpoint["discriminator_optimizer_state_dict"]
        )

    # 다음 학습이 이어질 시작 에포크 번호를 계산합니다.
    next_epoch = int(checkpoint["epoch"]) + 1

    # 저장된 생성자 손실 기록을 가져오며 없으면 빈 목록을 사용합니다.
    generator_losses = list(checkpoint.get("generator_losses", []))

    # 저장된 판별자 손실 기록을 가져오며 없으면 빈 목록을 사용합니다.
    discriminator_losses = list(checkpoint.get("discriminator_losses", []))

    # 다음 에포크 번호와 두 손실 기록을 반환합니다.
    return next_epoch, generator_losses, discriminator_losses
