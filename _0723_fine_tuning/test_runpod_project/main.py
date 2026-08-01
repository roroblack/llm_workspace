# PyTorch 라이브러리를 불러옵니다.
import torch

# 현재 실행 중인 PyTorch 버전을 출력합니다.
print("PyTorch 버전:", torch.__version__)

# CUDA GPU 를 사용할 수 있는지 확인합니다.
print("CUDA 사용 가능:", torch.cuda.is_available())

# CUDA 를 사용할 수 있다면 현재 GPU 이름을 출력합니다.
if torch.cuda.is_available():
    print("GPU 이름:", torch.cuda.get_device_name(0))
else:
    print("사용 가능한 CUDA GPU 가 없습니다.")