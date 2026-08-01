"""
GAN 프로젝트의 공통 설정값을 관리하는 모듈입니다.

이 파일에서 학습 횟수, 배치 크기, 잠재 벡터 크기, 학습률,
출력 경로 등을 한 곳에서 변경할 수 있습니다.
"""

# dataclass 데코레이터를 사용하기 위해 dataclasses 모듈에서 dataclass를 가져옵니다.
from dataclasses import dataclass

# 운영체제와 관계없이 경로를 안전하게 처리하기 위해 pathlib의 Path 클래스를 가져옵니다.
from pathlib import Path

# PyTorch의 텐서 연산과 GPU 사용 여부 확인을 위해 torch 패키지를 가져옵니다.
import torch


# 설정값을 하나의 객체로 관리하기 위해 dataclass 데코레이터를 적용합니다.
@dataclass
class GANConfig:
    """GAN 학습과 실행에 필요한 설정값을 보관하는 클래스입니다."""

    # 프로젝트 최상위 디렉터리의 절대 경로를 저장합니다.
    project_root: Path = Path(__file__).resolve().parent

    # MNIST 데이터셋을 내려받고 저장할 디렉터리를 지정합니다.
    data_dir: Path = project_root / "data"

    # 생성 이미지, 체크포인트, 그래프를 저장할 상위 디렉터리를 지정합니다.
    output_dir: Path = project_root / "outputs"

    # 생성자가 만든 이미지를 저장할 디렉터리를 지정합니다.
    generated_dir: Path = output_dir / "generated"

    # 학습된 모델의 가중치를 저장할 디렉터리를 지정합니다.
    checkpoint_dir: Path = output_dir / "checkpoints"

    # 손실 변화 그래프를 저장할 디렉터리를 지정합니다.
    plot_dir: Path = output_dir / "plots"

    # 한 번의 학습 단계에서 사용할 이미지 개수를 지정합니다.
    batch_size: int = 128

    # 생성자의 입력으로 사용할 잠재 벡터의 차원 수를 지정합니다.
    latent_dim: int = 100

    # MNIST 이미지의 높이를 지정합니다.
    image_height: int = 28

    # MNIST 이미지의 너비를 지정합니다.
    image_width: int = 28

    # MNIST가 흑백 이미지이므로 채널 수를 1로 지정합니다.
    image_channels: int = 1

    # 기본 학습 반복 횟수인 에포크 수를 지정합니다.
    epochs: int = 20

    # 생성자와 판별자 옵티마이저에 사용할 학습률을 지정합니다.
    learning_rate: float = 0.0002

    # Adam 옵티마이저의 첫 번째 모멘텀 계수를 지정합니다.
    beta1: float = 0.5

    # Adam 옵티마이저의 두 번째 모멘텀 계수를 지정합니다.
    beta2: float = 0.999

    # DataLoader가 데이터를 읽을 때 사용할 보조 프로세스 수를 지정합니다.
    num_workers: int = 0

    # 실행 결과를 재현하기 위한 난수 시드값을 지정합니다.
    random_seed: int = 42

    # 학습 진행 상황을 몇 배치마다 출력할지 지정합니다.
    log_interval: int = 100

    # 생성 결과를 확인할 고정 잠재 벡터의 개수를 지정합니다.
    sample_count: int = 64

    @property
    def flattened_image_size(self) -> int:
        """한 장의 이미지를 1차원 벡터로 펼쳤을 때의 원소 수를 반환합니다."""

        # 채널 수, 높이, 너비를 곱하여 전체 픽셀 원소 수를 계산합니다.
        return self.image_channels * self.image_height * self.image_width

    @property
    def device(self) -> torch.device:
        """CUDA GPU 사용 가능 여부에 따라 실행 장치를 반환합니다."""

        # CUDA를 사용할 수 있으면 GPU 장치를, 그렇지 않으면 CPU 장치를 선택합니다.
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def create_directories(self) -> None:
        """프로젝트 실행에 필요한 데이터 및 출력 디렉터리를 생성합니다."""

        # 데이터 저장 폴더가 없으면 상위 폴더까지 포함하여 생성합니다.
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 생성 이미지 저장 폴더가 없으면 상위 폴더까지 포함하여 생성합니다.
        self.generated_dir.mkdir(parents=True, exist_ok=True)

        # 체크포인트 저장 폴더가 없으면 상위 폴더까지 포함하여 생성합니다.
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # 그래프 저장 폴더가 없으면 상위 폴더까지 포함하여 생성합니다.
        self.plot_dir.mkdir(parents=True, exist_ok=True)
