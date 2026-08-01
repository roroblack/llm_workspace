"""
mock 또는 Transformers 모델을 사용하여 답변을 생성하는 서비스입니다.
"""

# 사용하지 않는 모델을 GPU 메모리에서 해제하기 위해 gc를 가져옵니다.
import gc

# 답변 생성 시간을 측정하기 위해 time을 가져옵니다.
import time

# 여러 스레드가 동시에 모델을 적재하지 못하도록 Lock을 가져옵니다.
from threading import Lock

# 설정 값을 읽기 위해 Settings와 get_settings를 가져옵니다.
from app.core.config import Settings, get_settings

# API 요청과 응답 스키마를 가져옵니다.
from app.models.schemas import GenerationRequest, GenerationResponse, ModelKind


class InferenceService:
    """
    요청된 모델을 필요할 때 적재하고 답변을 생성합니다.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """
        설정과 모델 캐시를 초기화합니다.
        """

        # 외부에서 설정을 전달하지 않으면 전역 설정을 사용합니다.
        self.settings = settings or get_settings()

        # 현재 메모리에 올라간 모델의 종류를 기록합니다.
        self._loaded_model_kind: ModelKind | None = None

        # Transformers 토크나이저 객체를 저장할 공간입니다.
        self._tokenizer = None

        # Transformers 모델 객체를 저장할 공간입니다.
        self._model = None

        # 동시에 두 요청이 모델을 교체하지 않도록 잠금 객체를 생성합니다.
        self._load_lock = Lock()

    def _model_path(self, model_kind: ModelKind) -> str:
        """
        모델 구분에 맞는 실제 경로를 반환합니다.
        """

        # base 요청이면 기반 모델 경로를 반환합니다.
        if model_kind == "base":
            return self.settings.base_model_path

        # fine_tuned 요청이면 파인튜닝 모델 경로를 반환합니다.
        return self.settings.fine_tuned_model_path

    def _mock_answer(self, prompt: str, model_kind: ModelKind) -> str:
        """
        GPU 모델 없이 API 흐름을 검증할 수 있는 모의 답변을 생성합니다.
        """

        # JSON 형식 요청이 포함된 경우 형식 평가가 가능하도록 JSON 문자열을 반환합니다.
        if "JSON" in prompt.upper() or "json" in prompt:
            return (
                '{"model":"' + model_kind + '",'
                '"result":"모의 평가 응답",'
                '"valid":true}'
            )

        # 파인튜닝 모델은 조금 더 구조화된 모의 답변을 반환합니다.
        if model_kind == "fine_tuned":
            return (
                "파인튜닝 모델 모의 답변입니다. "
                "질문의 핵심을 먼저 설명하고, 평가 기준과 적용 절차를 "
                "구분하여 안내합니다."
            )

        # Base 모델의 비교 기준이 되는 간단한 모의 답변을 반환합니다.
        return "기반 모델 모의 답변입니다. 질문에 대한 일반적인 설명입니다."

    def _clear_loaded_model(self) -> None:
        """
        현재 적재된 모델과 토크나이저를 메모리에서 제거합니다.
        """

        # 모델 참조를 제거합니다.
        self._model = None

        # 토크나이저 참조를 제거합니다.
        self._tokenizer = None

        # 현재 적재 모델 정보를 초기화합니다.
        self._loaded_model_kind = None

        # 파이썬이 참조되지 않는 객체를 정리하도록 요청합니다.
        gc.collect()

        try:
            # PyTorch가 설치된 환경에서만 torch를 가져옵니다.
            import torch

            # CUDA를 사용할 수 있으면 캐시 메모리를 반환합니다.
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            # 로컬 mock 환경에는 torch가 없을 수 있으므로 오류 없이 통과합니다.
            pass

    def _resolve_torch_dtype(self, torch_module):
        """
        문자열 설정을 실제 PyTorch dtype 객체로 변환합니다.
        """

        # 설정값을 소문자로 정규화합니다.
        dtype_name = self.settings.torch_dtype.lower()

        # auto는 Transformers가 자동으로 결정하도록 문자열을 그대로 반환합니다.
        if dtype_name == "auto":
            return "auto"

        # 지원할 dtype 이름과 PyTorch 객체의 대응표를 만듭니다.
        dtype_map = {
            "float16": torch_module.float16,
            "bfloat16": torch_module.bfloat16,
            "float32": torch_module.float32,
        }

        # 지원하지 않는 값이면 명확한 오류를 발생시킵니다.
        if dtype_name not in dtype_map:
            raise ValueError(
                "TORCH_DTYPE은 auto, float16, bfloat16, float32 중 하나여야 합니다."
            )

        # 변환된 PyTorch dtype을 반환합니다.
        return dtype_map[dtype_name]

    def _ensure_transformers_model(self, model_kind: ModelKind) -> None:
        """
        요청된 Transformers 모델이 메모리에 없으면 새로 적재합니다.
        """

        # 이미 같은 종류의 모델이 적재되어 있으면 다시 로드하지 않습니다.
        if self._loaded_model_kind == model_kind and self._model is not None:
            return

        # 모델 적재 구간을 잠가 중복 적재를 방지합니다.
        with self._load_lock:
            # 잠금 대기 중 다른 요청이 이미 적재했을 수 있으므로 다시 확인합니다.
            if self._loaded_model_kind == model_kind and self._model is not None:
                return

            # 기존 모델을 먼저 메모리에서 제거합니다.
            self._clear_loaded_model()

            try:
                # 실제 추론에 필요한 PyTorch를 가져옵니다.
                import torch

                # Hugging Face 모델과 토크나이저 클래스를 가져옵니다.
                from transformers import AutoModelForCausalLM, AutoTokenizer
            except ImportError as error:
                # RunPod 의존성이 설치되지 않았음을 알 수 있는 오류를 제공합니다.
                raise RuntimeError(
                    "transformers 백엔드를 사용하려면 "
                    "requirements-runpod.txt를 설치해야 합니다."
                ) from error

            # 선택한 모델의 실제 경로를 확인합니다.
            model_path = self._model_path(model_kind)

            # Hugging Face 인증 토큰이 있을 때만 전달할 공통 인자를 구성합니다.
            common_kwargs = {}
            if self.settings.hf_token:
                common_kwargs["token"] = self.settings.hf_token

            # 모델과 동일한 저장소에서 토크나이저를 불러옵니다.
            tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True,
                **common_kwargs,
            )

            # 패딩 토큰이 없는 Causal LLM은 종료 토큰을 패딩 토큰으로 사용합니다.
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token

            # 모델 로딩 인자를 구성합니다.
            model_kwargs = {
                "device_map": self.settings.device_map,
                "torch_dtype": self._resolve_torch_dtype(torch),
                "trust_remote_code": True,
                **common_kwargs,
            }

            # 4비트 로딩을 요청한 경우 BitsAndBytes 설정을 추가합니다.
            if self.settings.load_in_4bit:
                from transformers import BitsAndBytesConfig

                # NF4 방식의 4비트 양자화 설정을 생성합니다.
                model_kwargs["quantization_config"] = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_compute_dtype=torch.bfloat16,
                )

            # Causal Language Model을 실제 GPU 또는 지정 장치에 적재합니다.
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                **model_kwargs,
            )

            # Dropout 등을 비활성화하여 추론 모드로 전환합니다.
            model.eval()

            # 적재한 객체를 서비스 캐시에 저장합니다.
            self._tokenizer = tokenizer
            self._model = model
            self._loaded_model_kind = model_kind

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """
        요청 설정에 따라 모의 답변 또는 실제 모델 답변을 생성합니다.
        """

        # 설정된 백엔드 이름을 소문자로 정규화합니다.
        backend = self.settings.inference_backend.lower()

        # 선택한 모델의 실제 경로를 계산합니다.
        model_path = self._model_path(request.model_kind)

        # mock 모드에서는 모델 다운로드 없이 즉시 결과를 만듭니다.
        if backend == "mock":
            # 모의 생성 시작 시각을 기록합니다.
            started_at = time.perf_counter()

            # 요청 모델에 맞는 모의 답변을 생성합니다.
            answer = self._mock_answer(request.prompt, request.model_kind)

            # 단순 공백 분리를 이용해 모의 토큰 수를 계산합니다.
            input_tokens = max(1, len(request.prompt.split()))
            output_tokens = max(1, len(answer.split()))

            # 실제 경과 시간을 계산하되 0으로 나눔을 방지합니다.
            latency = max(time.perf_counter() - started_at, 0.000001)

            # 구조화된 API 응답 객체를 반환합니다.
            return GenerationResponse(
                backend=backend,
                model_kind=request.model_kind,
                model_path=model_path,
                prompt=request.prompt,
                answer=answer,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_seconds=latency,
                tokens_per_second=output_tokens / latency,
            )

        # 지원하는 실제 추론 백엔드인지 확인합니다.
        if backend != "transformers":
            raise ValueError(
                "INFERENCE_BACKEND는 mock 또는 transformers여야 합니다."
            )

        # 요청된 실제 모델을 메모리에 적재합니다.
        self._ensure_transformers_model(request.model_kind)

        # 정적 타입 검사와 실행 안정성을 위해 로컬 변수에 저장합니다.
        tokenizer = self._tokenizer
        model = self._model

        # 모델 또는 토크나이저가 없으면 비정상 상태이므로 오류를 발생시킵니다.
        if tokenizer is None or model is None:
            raise RuntimeError("모델 적재에 실패했습니다.")

        # PyTorch 추론 기능을 사용하기 위해 가져옵니다.
        import torch

        # 모델이 지켜야 할 기본 시스템 지시문을 구성합니다.
        messages = [
            {
                "role": "system",
                "content": (
                    "당신은 정확하고 자연스러운 한국어로 답하는 AI 도우미입니다. "
                    "확실하지 않은 사실을 임의로 만들지 마세요."
                ),
            },
            {
                "role": "user",
                "content": request.prompt,
            },
        ]

        # 해당 모델이 제공하는 채팅 템플릿으로 메시지를 문자열화합니다.
        prompt_text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        # 프롬프트 문자열을 PyTorch 입력 텐서로 변환합니다.
        model_inputs = tokenizer(
            prompt_text,
            return_tensors="pt",
        )

        # 모델의 첫 번째 파라미터가 위치한 장치를 확인합니다.
        model_device = next(model.parameters()).device

        # 각 입력 텐서를 모델이 위치한 장치로 이동합니다.
        model_inputs = {
            key: value.to(model_device)
            for key, value in model_inputs.items()
        }

        # 정확한 GPU 시간 측정을 위해 이전 CUDA 작업을 완료합니다.
        if torch.cuda.is_available():
            torch.cuda.synchronize()

        # 답변 생성 시작 시각을 기록합니다.
        started_at = time.perf_counter()

        # 평가에서는 역전파가 필요하지 않으므로 추론 모드를 사용합니다.
        with torch.inference_mode():
            generated_ids = model.generate(
                **model_inputs,
                max_new_tokens=request.max_new_tokens,
                do_sample=request.do_sample,
                temperature=request.temperature if request.do_sample else None,
                top_p=request.top_p if request.do_sample else None,
                eos_token_id=tokenizer.eos_token_id,
                pad_token_id=tokenizer.pad_token_id,
            )

        # CUDA 생성 작업이 끝날 때까지 기다립니다.
        if torch.cuda.is_available():
            torch.cuda.synchronize()

        # 전체 생성 시간을 계산합니다.
        latency = max(time.perf_counter() - started_at, 0.000001)

        # 입력 토큰 길이를 계산합니다.
        input_tokens = int(model_inputs["input_ids"].shape[1])

        # 전체 출력에서 입력 프롬프트 이후의 새 토큰만 분리합니다.
        answer_token_ids = generated_ids[0][input_tokens:]

        # 새로 생성된 토큰 수를 계산합니다.
        output_tokens = int(answer_token_ids.shape[0])

        # 토큰 ID를 특수 토큰을 제외한 문자열로 변환합니다.
        answer = tokenizer.decode(
            answer_token_ids,
            skip_special_tokens=True,
        ).strip()

        # 최종 추론 결과를 반환합니다.
        return GenerationResponse(
            backend=backend,
            model_kind=request.model_kind,
            model_path=model_path,
            prompt=request.prompt,
            answer=answer,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_seconds=latency,
            tokens_per_second=output_tokens / latency,
        )


# 애플리케이션 전체에서 재사용할 단일 서비스 객체를 생성합니다.
inference_service = InferenceService()
