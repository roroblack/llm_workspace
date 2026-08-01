"""
MNIST 데이터셋을 내려받고 DataLoader로 구성하는 모듈입니다.
"""

# PyTorch의 DataLoader 클래스를 사용하기 위해 가져옵니다.
from torch.utils.data import DataLoader

# MNIST 데이터셋과 이미지 전처리 기능을 사용하기 위해 torchvision 모듈을 가져옵니다.
from torchvision import datasets, transforms

# 프로젝트 공통 설정 클래스를 가져옵니다.
from config import GANConfig


# MNIST 학습용 DataLoader를 생성하는 함수를 정의합니다.
def create_mnist_dataloader(config: GANConfig) -> DataLoader:
    """MNIST 이미지를 -1~1 범위로 정규화하여 배치 단위로 반환합니다."""

    # 여러 이미지 변환 과정을 순서대로 적용하는 전처리 파이프라인을 정의합니다.
    transform = transforms.Compose(
        [
            # PIL 이미지를 PyTorch 텐서로 변환하고 픽셀 범위를 0~1로 바꿉니다.
            transforms.ToTensor(),

            # 평균 0.5와 표준편차 0.5를 사용하여 픽셀 범위를 대략 -1~1로 변경합니다.
            transforms.Normalize(mean=(0.5,), std=(0.5,)),
        ]
    )

    # torchvision이 제공하는 MNIST 학습 데이터셋 객체를 생성합니다.
    dataset = datasets.MNIST(
        # 데이터셋을 저장할 로컬 디렉터리를 지정합니다.
        root=str(config.data_dir),

        # 학습용 데이터 60,000개를 사용하도록 지정합니다.
        train=True,

        # 데이터가 없을 경우 인터넷에서 자동으로 내려받도록 설정합니다.
        download=True,

        # 각 이미지에 위에서 정의한 전처리 파이프라인을 적용합니다.
        transform=transform,
    )

    # 데이터셋을 미니배치 단위로 공급하는 DataLoader를 생성합니다.
    dataloader = DataLoader(
        # DataLoader가 사용할 MNIST 데이터셋을 전달합니다.
        dataset=dataset,

        # 한 배치에 포함할 이미지 수를 설정합니다.
        batch_size=config.batch_size,

        # 매 에포크마다 데이터 순서를 무작위로 섞습니다.
        shuffle=True,

        # 데이터를 읽을 보조 프로세스 수를 설정합니다.
        num_workers=config.num_workers,

        # 마지막 배치의 크기가 작아도 버리지 않고 학습에 사용합니다.
        drop_last=False,

        # GPU 사용 시 CPU 고정 메모리를 사용하여 전송 효율을 높입니다.
        pin_memory=config.device.type == "cuda",
    )

    # 완성된 DataLoader를 호출한 코드에 반환합니다.
    return dataloader
