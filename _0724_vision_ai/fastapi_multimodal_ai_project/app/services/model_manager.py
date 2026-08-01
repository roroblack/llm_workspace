"""AI 모델을 필요할 때 한 번만 로딩하여 재사용하는 지연 로딩 관리자입니다."""

# 여러 요청이 동시에 모델을 로딩하지 못하도록 잠금 객체를 사용합니다.
from threading import Lock

# 타입 힌트에서 어떤 객체도 저장할 수 있도록 Any를 가져옵니다.
from typing import Any

# PyTorch를 사용하여 CPU 또는 CUDA 장치를 자동 선택합니다.
import torch

# 애플리케이션 설정을 가져옵니다.
from app.config import settings


class ModelManager:
    """BLIP, Stable Diffusion, Whisper 모델의 단일 인스턴스를 관리합니다."""

    # 각 모델의 초기값은 아직 로딩하지 않았음을 나타내는 None입니다.
    _caption_processor: Any = None
    _caption_model: Any = None
    _translation_tokenizer: Any = None
    _translation_model: Any = None
    _diffusion_pipeline: Any = None
    _whisper_processor: Any = None
    _whisper_model: Any = None

    # 모델별 로딩 과정에서 경쟁 상태를 방지하는 잠금 객체입니다.
    _caption_lock = Lock()
    _translation_lock = Lock()
    _diffusion_lock = Lock()
    _whisper_lock = Lock()

    @staticmethod
    def torch_device() -> str:
        """CUDA 사용 가능 여부에 따라 PyTorch 연산 장치를 반환합니다."""

        # NVIDIA CUDA GPU가 사용 가능하면 cuda를, 아니면 cpu를 선택합니다.
        return "cuda" if torch.cuda.is_available() else "cpu"

    @classmethod
    def get_caption_components(cls) -> tuple[Any, Any]:
        """BLIP 프로세서와 캡셔닝 모델을 최초 한 번만 로딩합니다."""

        # 두 객체가 이미 로딩되어 있으면 즉시 재사용합니다.
        if cls._caption_processor is not None and cls._caption_model is not None:
            return cls._caption_processor, cls._caption_model

        # 동시에 여러 요청이 들어와도 한 스레드만 모델을 로딩하도록 잠급니다.
        with cls._caption_lock:
            # 잠금을 기다리는 동안 다른 스레드가 모델을 로딩했는지 다시 확인합니다.
            if cls._caption_processor is None or cls._caption_model is None:
                # 무거운 transformers 모듈은 실제 사용 시점에 가져와 서버 시작을 빠르게 합니다.
                from transformers import BlipForConditionalGeneration, BlipProcessor

                # 이미지와 텍스트를 모델 입력 형태로 변환할 프로세서를 다운로드하고 로딩합니다.
                cls._caption_processor = BlipProcessor.from_pretrained(settings.caption_model_id)

                # 이미지 특징을 바탕으로 문장을 생성할 BLIP 모델을 로딩합니다.
                cls._caption_model = BlipForConditionalGeneration.from_pretrained(
                    settings.caption_model_id
                )

                # 선택한 CPU 또는 GPU 장치로 모델을 이동합니다.
                cls._caption_model.to(cls.torch_device())

                # 추론 전용 모드로 변경하여 Dropout 같은 학습 동작을 비활성화합니다.
                cls._caption_model.eval()

        # 로딩된 프로세서와 모델을 반환합니다.
        return cls._caption_processor, cls._caption_model


    @classmethod
    def get_translation_components(cls) -> tuple[Any, Any]:
        """영어 캡션을 한국어로 번역할 NLLB 토크나이저와 모델을 로딩합니다."""

        # 이미 로딩된 토크나이저와 모델이 있으면 다시 다운로드하지 않고 재사용합니다.
        if cls._translation_tokenizer is not None and cls._translation_model is not None:
            return cls._translation_tokenizer, cls._translation_model

        # 여러 요청이 동시에 번역 모델을 중복 로딩하지 않도록 잠금을 사용합니다.
        with cls._translation_lock:
            # 잠금 대기 중 다른 요청이 모델을 준비했는지 다시 확인합니다.
            if cls._translation_tokenizer is None or cls._translation_model is None:
                # NLLB는 Auto 계열 클래스로 로딩해야 언어 코드와 모델 구성이 올바르게 적용됩니다.
                from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

                # 소스 언어를 영어로 고정하여 영어 캡션 토큰화를 안정화합니다.
                cls._translation_tokenizer = AutoTokenizer.from_pretrained(
                    settings.translation_model_id,
                    src_lang="eng_Latn",
                    use_fast=True,
                )

                # 객체와 행동 보존 성능이 좋은 NLLB 번역 모델을 로딩합니다.
                cls._translation_model = AutoModelForSeq2SeqLM.from_pretrained(
                    settings.translation_model_id,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    low_cpu_mem_usage=True,
                )

                # 현재 실행 환경의 CPU 또는 CUDA 장치로 모델을 이동합니다.
                cls._translation_model.to(cls.torch_device())

                # 학습 동작을 끄고 추론 모드로 설정합니다.
                cls._translation_model.eval()

        # 준비된 토크나이저와 모델을 반환합니다.
        return cls._translation_tokenizer, cls._translation_model

    @classmethod
    def get_diffusion_pipeline(cls) -> Any:
        """Stable Diffusion 파이프라인을 최초 한 번만 로딩합니다."""

        # 파이프라인이 이미 있으면 다시 다운로드하지 않고 재사용합니다.
        if cls._diffusion_pipeline is not None:
            return cls._diffusion_pipeline

        # 동시에 여러 요청이 파이프라인을 중복 로딩하지 않도록 잠급니다.
        with cls._diffusion_lock:
            # 잠금 획득 후 다른 요청이 먼저 로딩했는지 다시 확인합니다.
            if cls._diffusion_pipeline is None:
                # diffusers 모듈을 실제 이미지 생성 시점에 가져옵니다.
                from diffusers import DiffusionPipeline

                # CUDA에서는 메모리를 절약하는 float16, CPU에서는 호환성이 높은 float32를 사용합니다.
                dtype = torch.float16 if torch.cuda.is_available() else torch.float32

                # 사전 학습 Stable Diffusion 구성 요소 전체를 로딩합니다.
                pipeline = DiffusionPipeline.from_pretrained(
                    settings.diffusion_model_id,
                    torch_dtype=dtype,
                    use_safetensors=True,
                )

                # GPU가 있으면 모든 구성 요소를 GPU로 이동합니다.
                if torch.cuda.is_available():
                    pipeline = pipeline.to("cuda")

                    # Attention 메모리 사용량을 줄이기 위해 슬라이싱을 활성화합니다.
                    pipeline.enable_attention_slicing()

                    # VAE 디코딩 메모리를 줄여 SDXL의 1024 해상도 생성을 안정화합니다.
                    if hasattr(pipeline, "enable_vae_slicing"):
                        pipeline.enable_vae_slicing()

                    # 지원되는 환경에서는 VAE 타일링으로 GPU 메모리 사용량을 더 낮춥니다.
                    if hasattr(pipeline, "enable_vae_tiling"):
                        pipeline.enable_vae_tiling()
                else:
                    # CPU 환경에서는 명시적으로 CPU 장치를 사용합니다.
                    pipeline = pipeline.to("cpu")

                # 진행률 표시줄을 끄고 서버 콘솔 로그를 간결하게 유지합니다.
                pipeline.set_progress_bar_config(disable=True)

                # 완성된 파이프라인을 클래스 변수에 저장합니다.
                cls._diffusion_pipeline = pipeline

        # 준비된 파이프라인을 반환합니다.
        return cls._diffusion_pipeline

    @classmethod
    def get_whisper_components(cls) -> tuple[Any, Any]:
        """PyTorch 기반 Whisper 프로세서와 모델을 최초 한 번만 로딩합니다.

        faster-whisper는 Windows에서 CTranslate2 네이티브 DLL이 보안 정책에 의해
        차단될 수 있습니다. 이 프로젝트는 해당 DLL을 전혀 사용하지 않는
        transformers의 WhisperForConditionalGeneration을 사용합니다.
        """

        # 프로세서와 모델이 모두 준비되어 있으면 메모리에 있는 객체를 재사용합니다.
        if cls._whisper_processor is not None and cls._whisper_model is not None:
            return cls._whisper_processor, cls._whisper_model

        # 여러 STT 요청이 동시에 최초 로딩을 시도하지 못하도록 잠금을 획득합니다.
        with cls._whisper_lock:
            # 잠금을 기다리는 동안 다른 요청이 로딩했는지 다시 확인합니다.
            if cls._whisper_processor is None or cls._whisper_model is None:
                # 네이티브 CTranslate2 DLL이 필요 없는 Hugging Face Whisper 클래스를 가져옵니다.
                from transformers import WhisperForConditionalGeneration, WhisperProcessor

                # 음성 파형을 Whisper 입력 특징으로 바꾸고 결과 토큰을 문장으로 복원할 프로세서입니다.
                cls._whisper_processor = WhisperProcessor.from_pretrained(
                    settings.whisper_model_id
                )

                # PyTorch에서 직접 실행되는 Whisper 음성 인식 모델을 다운로드하고 로딩합니다.
                cls._whisper_model = WhisperForConditionalGeneration.from_pretrained(
                    settings.whisper_model_id,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    low_cpu_mem_usage=True,
                )

                # 현재 컴퓨터에서 사용 가능한 CPU 또는 CUDA 장치로 모델을 이동합니다.
                cls._whisper_model.to(cls.torch_device())

                # 학습 동작을 끄고 추론 결과와 메모리 사용을 안정화합니다.
                cls._whisper_model.eval()

        # 준비된 프로세서와 모델을 함께 반환합니다.
        return cls._whisper_processor, cls._whisper_model
