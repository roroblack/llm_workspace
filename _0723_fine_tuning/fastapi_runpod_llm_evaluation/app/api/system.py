"""
서버와 GPU 환경 상태를 확인하는 API 라우터입니다.
"""

# FastAPI 라우터 객체를 가져옵니다.
from fastapi import APIRouter

# 애플리케이션 설정을 가져옵니다.
from app.core.config import get_settings


# /api/system 경로 아래에서 사용할 라우터를 생성합니다.
router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/health")
def health() -> dict:
    """
    서버, 백엔드, CUDA 사용 가능 여부를 반환합니다.
    """

    # 현재 애플리케이션 설정을 읽습니다.
    settings = get_settings()

    try:
        # PyTorch가 설치되어 있으면 GPU 정보를 확인합니다.
        import torch

        # CUDA 사용 가능 여부를 계산합니다.
        cuda_available = torch.cuda.is_available()

        # CUDA를 사용할 수 있으면 첫 번째 GPU 이름을 읽습니다.
        gpu_name = (
            torch.cuda.get_device_name(0)
            if cuda_available
            else None
        )

        # 설치된 PyTorch 버전을 문자열로 읽습니다.
        torch_version = torch.__version__
    except ImportError:
        # 로컬 mock 환경에서 PyTorch가 없으면 GPU 정보를 기본값으로 처리합니다.
        cuda_available = False
        gpu_name = None
        torch_version = None

    # 상태 확인 결과를 JSON으로 반환합니다.
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "inference_backend": settings.inference_backend,
        "base_model_path": settings.base_model_path,
        "fine_tuned_model_path": settings.fine_tuned_model_path,
        "torch_version": torch_version,
        "cuda_available": cuda_available,
        "gpu_name": gpu_name,
    }
