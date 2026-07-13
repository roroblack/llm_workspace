"""재현성 설정, 장치 선택 등 여러 파일에서 공통으로 사용하는 유틸리티 함수입니다."""

import random

import numpy as np
import torch


def set_seed(seed: int) -> None:
    """Python, NumPy, PyTorch의 난수 시드를 고정합니다."""
    # Python 기본 random 모듈의 난수 시드를 고정하여 데이터 섞기 결과를 재현 가능하게 만듭니다.
    random.seed(seed)

    # NumPy 난수 시드를 고정하여 배열 기반 난수 결과를 재현 가능하게 만듭니다.
    np.random.seed(seed)

    # PyTorch CPU 연산에서 사용하는 난수 시드를 고정합니다.
    torch.manual_seed(seed)

    # CUDA GPU가 있는 경우 모든 GPU의 난수 시드를 함께 고정합니다.
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def get_device() -> torch.device:
    """CUDA 사용 가능 여부에 따라 GPU 또는 CPU 장치를 반환합니다."""
    # GPU가 사용 가능하면 cuda를 사용하고, 그렇지 않으면 cpu를 사용합니다.
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")
