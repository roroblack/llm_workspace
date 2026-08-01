"""
Qwen2.5-0.5B-Instruct 모델을 대상으로
한국어 고객 상담 데이터 SFT를 수행하는 전체 학습 코드입니다.

학습 방식:
    Supervised Fine-Tuning
    + 4bit Quantization
    + LoRA
    = QLoRA 기반 SFT
"""

# os 모듈은 환경변수 설정과 운영체제 기능을 사용할 때 필요합니다.
import os

# json 모듈은 학습 결과와 설정 정보를 JSON 파일로 저장할 때 사용합니다.
import json

# gc 모듈은 사용하지 않는 파이썬 객체를 정리하여
# 메모리를 확보하는 데 사용합니다.
import gc

# Path는 파일과 디렉터리 경로를 안전하게 처리합니다.
from pathlib import Path

# Any는 다양한 자료형을 허용하는 타입 힌트에 사용합니다.
from typing import Any

# PyTorch는 모델 학습과 GPU 연산을 담당합니다.
import torch

# .env 파일의 환경변수를 불러오기 위해 사용합니다.
from dotenv import load_dotenv

# Hugging Face datasets의 JSON 데이터 로더입니다.
from datasets import load_dataset

# Hugging Face 모델, Tokenizer 및 양자화 설정 클래스를 불러옵니다.
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    set_seed,
)

# LoRA 설정과 k-bit 학습 준비 함수를 불러옵니다.
from peft import (
    LoraConfig,
    prepare_model_for_kbit_training,
)

# TRL에서 SFT 전용 설정과 Trainer를 불러옵니다.
from trl import (
    SFTConfig,
    SFTTrainer,
)


# -------------------------------------------------------------------
# 1. 기본 경로 설정
# -------------------------------------------------------------------

# 현재 파이썬 파일이 위치한 디렉터리를 프로젝트 기준 경로로 지정합니다.
BASE_DIR = Path(__file__).resolve().parent

# 프로젝트 루트의 .env 파일을 읽습니다.
load_dotenv(BASE_DIR / ".env")

# 학습 데이터 파일 경로를 설정합니다.
TRAIN_FILE = BASE_DIR / "data" / "train.jsonl"

# 검증 데이터 파일 경로를 설정합니다.
VALID_FILE = BASE_DIR / "data" / "valid.jsonl"

# 환경변수에 MODEL_NAME이 있으면 해당 값을 사용하고,
# 없으면 Qwen2.5-0.5B-Instruct를 기본 모델로 사용합니다.
MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "Qwen/Qwen2.5-0.5B-Instruct",
)

# 환경변수에 OUTPUT_DIR이 있으면 해당 경로를 사용합니다.
OUTPUT_DIR = BASE_DIR / os.getenv(
    "OUTPUT_DIR",
    "outputs/qwen2.5-korean-sft-lora",
)

# Trainer가 중간 체크포인트를 저장할 경로입니다.
CHECKPOINT_DIR = BASE_DIR / "outputs" / "checkpoints"

# Hugging Face 접근 토큰을 환경변수에서 읽습니다.
HF_TOKEN = os.getenv("HF_TOKEN") or None

# 난수 시드를 고정하여 가능한 범위에서 학습 결과를 재현합니다.
SEED = 42


# -------------------------------------------------------------------
# 2. 학습 하이퍼파라미터
# -------------------------------------------------------------------

# 한 번에 모델에 입력할 최대 토큰 수입니다.
MAX_LENGTH = 512

# GPU에 한 번에 올릴 학습 데이터 개수입니다.
# GPU 메모리가 부족하면 1로 유지합니다.
TRAIN_BATCH_SIZE = 1

# 평가 과정에서 GPU에 한 번에 올릴 데이터 개수입니다.
EVAL_BATCH_SIZE = 1

# 여러 미니 배치의 Gradient를 누적할 횟수입니다.
# 실제 배치 크기는 TRAIN_BATCH_SIZE × GRADIENT_ACCUMULATION_STEPS입니다.
GRADIENT_ACCUMULATION_STEPS = 8

# 전체 학습 데이터를 반복할 횟수입니다.
NUM_TRAIN_EPOCHS = 3

# LoRA 학습에서 사용할 학습률입니다.
LEARNING_RATE = 2e-4

# 가중치가 과도하게 커지는 것을 억제하기 위한 Weight Decay입니다.
WEIGHT_DECAY = 0.01

# 학습률을 처음부터 바로 크게 적용하지 않고
# 점진적으로 증가시키는 Warm-up 비율입니다.
WARMUP_RATIO = 0.05

# 몇 Step마다 학습 상태와 Loss를 출력할지 지정합니다.
LOGGING_STEPS = 1

# 최대 몇 개의 체크포인트를 유지할지 지정합니다.
SAVE_TOTAL_LIMIT = 2


def print_environment() -> None:
    """
    현재 실행 환경의 Python, PyTorch, CUDA 및 GPU 정보를 출력합니다.
    """

    # 실행 환경 구분선을 출력합니다.
    print("=" * 80)
    print("1. 실행 환경 확인")
    print("=" * 80)

    # 현재 설치된 PyTorch 버전을 출력합니다.
    print(f"PyTorch 버전       : {torch.__version__}")

    # CUDA 사용 가능 여부를 출력합니다.
    print(f"CUDA 사용 가능     : {torch.cuda.is_available()}")

    # CUDA를 사용할 수 있는 경우 GPU 정보를 추가로 출력합니다.
    if torch.cuda.is_available():

        # 사용 가능한 GPU 개수를 출력합니다.
        print(f"GPU 개수            : {torch.cuda.device_count()}")

        # 첫 번째 GPU의 이름을 출력합니다.
        print(f"GPU 이름            : {torch.cuda.get_device_name(0)}")

        # 현재 PyTorch가 사용하는 CUDA 버전을 출력합니다.
        print(f"PyTorch CUDA 버전   : {torch.version.cuda}")

        # 전체 GPU 메모리를 Byte 단위에서 GB 단위로 변환합니다.
        total_memory_gb = (
            torch.cuda.get_device_properties(0).total_memory
            / 1024**3
        )

        # 전체 GPU 메모리를 출력합니다.
        print(f"GPU 전체 메모리     : {total_memory_gb:.2f} GB")

    else:
        # QLoRA 학습은 NVIDIA GPU 환경에서 실행할 것을 안내합니다.
        print(
            "경고: CUDA GPU가 감지되지 않았습니다. "
            "4bit QLoRA 학습은 NVIDIA GPU 환경에서 실행해야 합니다."
        )


def validate_files() -> None:
    """
    학습 전에 필요한 데이터 파일이 존재하는지 확인합니다.
    """

    # 학습 데이터가 존재하지 않으면 FileNotFoundError를 발생시킵니다.
    if not TRAIN_FILE.exists():
        raise FileNotFoundError(
            f"학습 데이터가 없습니다: {TRAIN_FILE}\n"
            "먼저 python 01_create_dataset.py를 실행하세요."
        )

    # 검증 데이터가 존재하지 않으면 FileNotFoundError를 발생시킵니다.
    if not VALID_FILE.exists():
        raise FileNotFoundError(
            f"검증 데이터가 없습니다: {VALID_FILE}\n"
            "먼저 python 01_create_dataset.py를 실행하세요."
        )


def load_sft_datasets():
    """
    train.jsonl과 valid.jsonl 파일을
    Hugging Face Dataset 객체로 읽어옵니다.

    Returns:
        train_dataset: 학습 데이터셋
        valid_dataset: 검증 데이터셋
    """

    # JSONL 파일 경로를 train과 validation 이름으로 연결합니다.
    data_files = {
        "train": str(TRAIN_FILE),
        "validation": str(VALID_FILE),
    }

    # JSON 데이터셋을 Hugging Face DatasetDict 형식으로 로드합니다.
    dataset_dict = load_dataset(
        "json",
        data_files=data_files,
    )

    # train 분할을 학습 데이터셋으로 가져옵니다.
    train_dataset = dataset_dict["train"]

    # validation 분할을 검증 데이터셋으로 가져옵니다.
    valid_dataset = dataset_dict["validation"]

    # 데이터셋 정보를 출력합니다.
    print("\n" + "=" * 80)
    print("2. 데이터셋 로드")
    print("=" * 80)
    print(f"학습 데이터 수 : {len(train_dataset)}")
    print(f"검증 데이터 수 : {len(valid_dataset)}")
    print(f"데이터 컬럼     : {train_dataset.column_names}")

    # 첫 번째 학습 샘플을 확인합니다.
    print("\n첫 번째 학습 데이터:")
    print(
        json.dumps(
            train_dataset[0],
            ensure_ascii=False,
            indent=2,
        )
    )

    # 학습 및 검증 데이터셋을 반환합니다.
    return train_dataset, valid_dataset


def select_compute_dtype() -> torch.dtype:
    """
    GPU가 bfloat16 연산을 지원하면 bfloat16을 사용하고,
    지원하지 않으면 float16을 사용합니다.

    Returns:
        선택된 PyTorch 데이터 타입
    """

    # CUDA가 있고 GPU가 BF16을 지원하는지 검사합니다.
    if (
        torch.cuda.is_available()
        and torch.cuda.is_bf16_supported()
    ):
        # Ampere 계열 이상 GPU에서는 일반적으로 BF16을 사용할 수 있습니다.
        return torch.bfloat16

    # BF16을 사용할 수 없으면 FP16을 사용합니다.
    return torch.float16


def load_tokenizer():
    """
    사전 학습 모델의 Tokenizer를 불러오고
    Padding 관련 설정을 적용합니다.

    Returns:
        설정이 완료된 Tokenizer
    """

    # 모델 이름과 Tokenizer 로드 시작 정보를 출력합니다.
    print("\n" + "=" * 80)
    print("3. Tokenizer 로드")
    print("=" * 80)
    print(f"Tokenizer 모델 : {MODEL_NAME}")

    # Hugging Face Hub에서 모델에 맞는 Tokenizer를 불러옵니다.
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,

        # 원격 저장소에 사용자 정의 코드가 있을 경우 사용할 수 있게 합니다.
        trust_remote_code=True,

        # 비공개 또는 사용 승인이 필요한 모델에 접근할 때 토큰을 사용합니다.
        token=HF_TOKEN,
    )

    # 일부 모델은 pad_token이 지정되지 않을 수 있습니다.
    if tokenizer.pad_token is None:

        # 문장 종료 토큰을 Padding 토큰으로 사용합니다.
        tokenizer.pad_token = tokenizer.eos_token

    # Causal Language Model 학습에서는 오른쪽 Padding을 사용합니다.
    tokenizer.padding_side = "right"

    # 모델 설정에 사용할 pad_token_id를 확인합니다.
    print(f"PAD Token          : {tokenizer.pad_token}")
    print(f"PAD Token ID       : {tokenizer.pad_token_id}")
    print(f"EOS Token          : {tokenizer.eos_token}")
    print(f"EOS Token ID       : {tokenizer.eos_token_id}")

    # 설정된 Tokenizer를 반환합니다.
    return tokenizer


def create_quantization_config(
    compute_dtype: torch.dtype,
) -> BitsAndBytesConfig:
    """
    4bit QLoRA 학습을 위한 BitsAndBytesConfig를 생성합니다.

    Args:
        compute_dtype: 실제 계산에 사용할 FP16 또는 BF16 타입입니다.

    Returns:
        4bit 양자화 설정 객체
    """

    # BitsAndBytes의 4bit 양자화 설정을 생성합니다.
    quantization_config = BitsAndBytesConfig(

        # 모델 가중치를 4bit로 로드합니다.
        load_in_4bit=True,

        # QLoRA에서 일반적으로 사용하는 NF4 양자화 방식을 적용합니다.
        bnb_4bit_quant_type="nf4",

        # 양자화 상수를 다시 양자화하여 메모리 사용량을 추가로 줄입니다.
        bnb_4bit_use_double_quant=True,

        # 행렬 연산은 FP16 또는 BF16으로 수행합니다.
        bnb_4bit_compute_dtype=compute_dtype,
    )

    # 생성한 양자화 설정을 반환합니다.
    return quantization_config


def load_quantized_model(
    tokenizer,
    compute_dtype: torch.dtype,
):
    """
    사전 학습 모델을 4bit로 불러오고
    k-bit 학습이 가능하도록 전처리합니다.

    Args:
        tokenizer: 모델 Tokenizer
        compute_dtype: 연산에 사용할 데이터 타입

    Returns:
        QLoRA 학습 준비가 완료된 모델
    """

    # 모델 로드 정보를 출력합니다.
    print("\n" + "=" * 80)
    print("4. 4bit 사전 학습 모델 로드")
    print("=" * 80)
    print(f"모델 이름          : {MODEL_NAME}")
    print(f"계산 데이터 타입   : {compute_dtype}")

    # 앞에서 정의한 함수로 4bit 양자화 설정을 생성합니다.
    quantization_config = create_quantization_config(
        compute_dtype=compute_dtype,
    )

    # Hugging Face Hub에서 Causal Language Model을 불러옵니다.
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,

        # 4bit 양자화 설정을 전달합니다.
        quantization_config=quantization_config,

        # 단일 GPU 환경에서 모델을 첫 번째 GPU에 배치합니다.
        device_map={"": 0},

        # 원격 저장소의 사용자 정의 모델 코드를 허용합니다.
        trust_remote_code=True,

        # 비공개 모델 접근용 Hugging Face 토큰입니다.
        token=HF_TOKEN,
    )

    # Tokenizer와 동일한 Padding Token ID를 모델 설정에도 지정합니다.
    model.config.pad_token_id = tokenizer.pad_token_id

    # 학습 과정에서 캐시를 사용하면 Gradient Checkpointing과
    # 충돌할 수 있으므로 캐시 사용을 비활성화합니다.
    model.config.use_cache = False

    # 양자화된 모델을 LoRA 학습에 적합한 형태로 준비합니다.
    model = prepare_model_for_kbit_training(
        model,

        # Gradient Checkpointing을 사용할 수 있도록 입력 Gradient를 준비합니다.
        use_gradient_checkpointing=True,
    )

    # 모델의 Gradient Checkpointing 기능을 활성화합니다.
    model.gradient_checkpointing_enable()

    # 준비된 모델을 반환합니다.
    return model


def create_lora_config() -> LoraConfig:
    """
    Qwen 계열 Causal Language Model에 적용할
    LoRA Adapter 설정을 생성합니다.

    Returns:
        LoraConfig 객체
    """

    # LoRA 설정 생성 시작을 출력합니다.
    print("\n" + "=" * 80)
    print("5. LoRA 설정")
    print("=" * 80)

    # LoRA Adapter의 세부 설정을 정의합니다.
    lora_config = LoraConfig(

        # 저차원 행렬의 Rank입니다.
        # 값이 크면 표현력은 증가하지만 학습 파라미터와 메모리도 증가합니다.
        r=16,

        # LoRA 출력에 적용되는 Scaling 계수입니다.
        lora_alpha=32,

        # 과적합을 줄이기 위해 LoRA 경로에 적용할 Dropout 비율입니다.
        lora_dropout=0.05,

        # 기존 Linear Layer의 Bias는 학습하지 않습니다.
        bias="none",

        # 현재 모델이 다음 토큰을 생성하는 Causal LM임을 지정합니다.
        task_type="CAUSAL_LM",

        # Qwen Transformer 내부에서 LoRA를 적용할 Linear Layer입니다.
        target_modules=[
            # Query Projection Layer입니다.
            "q_proj",

            # Key Projection Layer입니다.
            "k_proj",

            # Value Projection Layer입니다.
            "v_proj",

            # Attention Output Projection Layer입니다.
            "o_proj",

            # Feed Forward Network의 Gate Layer입니다.
            "gate_proj",

            # Feed Forward Network의 확장 Projection Layer입니다.
            "up_proj",

            # Feed Forward Network의 축소 Projection Layer입니다.
            "down_proj",
        ],
    )

    # 주요 LoRA 설정값을 출력합니다.
    print(f"LoRA Rank          : {lora_config.r}")
    print(f"LoRA Alpha         : {lora_config.lora_alpha}")
    print(f"LoRA Dropout       : {lora_config.lora_dropout}")
    print(f"Target Modules     : {lora_config.target_modules}")

    # 생성된 LoRA 설정을 반환합니다.
    return lora_config


def create_training_config(
    compute_dtype: torch.dtype,
) -> SFTConfig:
    """
    SFTTrainer가 사용할 학습 하이퍼파라미터를 생성합니다.

    Args:
        compute_dtype: BF16 또는 FP16 중 사용할 연산 타입

    Returns:
        SFTConfig 객체
    """

    # BF16 사용 여부를 판단합니다.
    use_bf16 = compute_dtype == torch.bfloat16

    # FP16 사용 여부를 판단합니다.
    use_fp16 = compute_dtype == torch.float16

    # 출력 디렉터리가 없으면 생성합니다.
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # 체크포인트 디렉터리가 없으면 생성합니다.
    CHECKPOINT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # SFT 학습 설정을 생성합니다.
    training_config = SFTConfig(

        # 체크포인트와 Trainer 결과를 저장할 디렉터리입니다.
        output_dir=str(CHECKPOINT_DIR),

        # 전체 학습 Epoch 수입니다.
        num_train_epochs=NUM_TRAIN_EPOCHS,

        # GPU 한 개당 학습 배치 크기입니다.
        per_device_train_batch_size=TRAIN_BATCH_SIZE,

        # GPU 한 개당 평가 배치 크기입니다.
        per_device_eval_batch_size=EVAL_BATCH_SIZE,

        # Gradient를 누적할 Step 수입니다.
        gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,

        # LoRA 파라미터를 갱신할 학습률입니다.
        learning_rate=LEARNING_RATE,

        # 가중치 감쇠 계수입니다.
        weight_decay=WEIGHT_DECAY,

        # 학습률 Warm-up 비율입니다.
        warmup_ratio=WARMUP_RATIO,

        # Cosine 방식으로 학습률을 감소시킵니다.
        lr_scheduler_type="cosine",

        # AdamW 계열 Optimizer를 사용합니다.
        optim="paged_adamw_8bit",

        # 몇 Step마다 로그를 출력할지 지정합니다.
        logging_steps=LOGGING_STEPS,

        # 학습 로그를 첫 Step부터 기록합니다.
        logging_first_step=True,

        # 매 Epoch가 끝날 때 검증 데이터로 평가합니다.
        eval_strategy="epoch",

        # 매 Epoch가 끝날 때 체크포인트를 저장합니다.
        save_strategy="epoch",

        # 최대 체크포인트 보관 개수입니다.
        save_total_limit=SAVE_TOTAL_LIMIT,

        # 학습이 끝난 후 가장 좋은 모델을 자동으로 불러옵니다.
        load_best_model_at_end=True,

        # 최적 모델 선택 기준으로 validation loss를 사용합니다.
        metric_for_best_model="eval_loss",

        # Loss는 낮을수록 좋은 값이므로 greater_is_better를 False로 지정합니다.
        greater_is_better=False,

        # BF16 사용 여부를 설정합니다.
        bf16=use_bf16,

        # FP16 사용 여부를 설정합니다.
        fp16=use_fp16,

        # Gradient Checkpointing으로 GPU 메모리 사용량을 줄입니다.
        gradient_checkpointing=True,

        # Gradient Checkpointing에서 비재진입 방식을 사용합니다.
        gradient_checkpointing_kwargs={
            "use_reentrant": False,
        },

        # 모델에 입력할 최대 토큰 길이입니다.
        max_length=MAX_LENGTH,

        # 길이가 다른 문장을 하나로 묶어 Padding을 줄이는 옵션입니다.
        # 작은 실습 데이터에서는 False로 두는 것이 이해하기 쉽습니다.
        packing=False,

        # TensorBoard 형식으로 학습 로그를 저장합니다.
        report_to=["tensorboard"],

        # 데이터셋 처리 시 사용할 프로세스 수입니다.
        dataset_num_proc=1,

        # Trainer가 데이터 컬럼을 임의로 제거하지 않도록 합니다.
        remove_unused_columns=False,

        # 난수 시드를 지정합니다.
        seed=SEED,

        # 데이터 샘플링 관련 난수 시드입니다.
        data_seed=SEED,
    )

    # 학습 설정을 반환합니다.
    return training_config


def count_parameters(model) -> dict[str, Any]:
    """
    전체 파라미터와 실제 학습 가능한 파라미터 개수를 계산합니다.

    Args:
        model: 파라미터를 확인할 모델

    Returns:
        전체, 학습 가능, 학습 비율을 포함한 딕셔너리
    """

    # 전체 파라미터 개수의 누적값입니다.
    total_parameters = 0

    # requires_grad=True인 학습 가능 파라미터의 누적값입니다.
    trainable_parameters = 0

    # 모델의 모든 파라미터를 반복합니다.
    for parameter in model.parameters():

        # 현재 Tensor가 가진 전체 원소 수를 전체 파라미터에 더합니다.
        total_parameters += parameter.numel()

        # Gradient 계산 대상이면 학습 가능 파라미터에 더합니다.
        if parameter.requires_grad:
            trainable_parameters += parameter.numel()

    # 전체 대비 학습 가능 파라미터 비율을 계산합니다.
    trainable_ratio = (
        100 * trainable_parameters / total_parameters
        if total_parameters > 0
        else 0.0
    )

    # 계산 결과를 딕셔너리로 반환합니다.
    return {
        "total_parameters": total_parameters,
        "trainable_parameters": trainable_parameters,
        "trainable_ratio": trainable_ratio,
    }


def save_json(
    data: Any,
    file_path: Path,
) -> None:
    """
    파이썬 객체를 UTF-8 JSON 파일로 저장합니다.
    """

    # 부모 디렉터리가 존재하지 않으면 생성합니다.
    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # 지정한 경로를 UTF-8 쓰기 모드로 엽니다.
    with file_path.open("w", encoding="utf-8") as file:

        # 데이터가 Tensor 등 JSON 변환이 어려운 값을 포함할 수 있으므로
        # default=str을 지정해 문자열 변환을 허용합니다.
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
            default=str,
        )


def run_test_inference(
    model,
    tokenizer,
    question: str,
) -> str:
    """
    현재 학습된 모델을 사용하여 한 개의 질문에 답변을 생성합니다.

    Args:
        model: 학습된 모델
        tokenizer: 모델 Tokenizer
        question: 사용자 질문

    Returns:
        생성된 답변 문자열
    """

    # 추론 시 KV Cache를 사용하여 생성 속도를 높입니다.
    model.config.use_cache = True

    # 모델을 평가 모드로 변경하여 Dropout을 비활성화합니다.
    model.eval()

    # 모델에 전달할 대화형 메시지를 구성합니다.
    messages = [
        {
            "role": "system",
            "content": (
                "당신은 온라인 쇼핑몰의 고객 상담 AI입니다. "
                "고객의 질문에 친절하고 정확하게 답변하세요."
            ),
        },
        {
            "role": "user",
            "content": question,
        },
    ]

    # 모델 전용 Chat Template을 적용하여 대화를 하나의 문자열로 변환합니다.
    prompt_text = tokenizer.apply_chat_template(
        messages,

        # 토큰 ID가 아니라 문자열을 반환받습니다.
        tokenize=False,

        # 모델이 assistant 답변을 생성하도록 생성 시작 토큰을 추가합니다.
        add_generation_prompt=True,
    )

    # 변환된 프롬프트를 PyTorch Tensor로 Tokenizing합니다.
    inputs = tokenizer(
        prompt_text,
        return_tensors="pt",
    )

    # 입력 Tensor를 모델이 위치한 GPU로 이동합니다.
    inputs = {
        key: value.to(model.device)
        for key, value in inputs.items()
    }

    # Gradient 계산을 비활성화하여 추론 메모리를 절약합니다.
    with torch.inference_mode():

        # 모델로부터 새로운 토큰을 생성합니다.
        generated_ids = model.generate(
            **inputs,

            # 생성할 최대 신규 토큰 수입니다.
            max_new_tokens=200,

            # 샘플링 방식의 생성을 활성화합니다.
            do_sample=True,

            # 생성 결과의 무작위성을 조절합니다.
            temperature=0.7,

            # 누적 확률 상위 90% 토큰 중에서 샘플링합니다.
            top_p=0.9,

            # 반복 표현을 억제합니다.
            repetition_penalty=1.1,

            # Padding Token ID를 지정합니다.
            pad_token_id=tokenizer.pad_token_id,

            # EOS Token이 생성되면 답변 생성을 종료합니다.
            eos_token_id=tokenizer.eos_token_id,
        )

    # 입력 프롬프트 부분을 제외하고 새로 생성된 토큰만 추출합니다.
    new_tokens = generated_ids[
        :,
        inputs["input_ids"].shape[1]:
    ]

    # 토큰 ID를 사람이 읽을 수 있는 문자열로 변환합니다.
    answer = tokenizer.batch_decode(
        new_tokens,
        skip_special_tokens=True,
    )[0]

    # 앞뒤 공백을 제거한 답변을 반환합니다.
    return answer.strip()


def main() -> None:
    """
    데이터 로드부터 모델 학습, 저장, 평가 및 추론까지
    전체 SFT 파이프라인을 실행합니다.
    """

    # 동일한 난수 흐름을 사용하도록 전역 Seed를 고정합니다.
    set_seed(SEED)

    # CUDA 연산 성능과 재현성 관련 설정을 적용합니다.
    if torch.cuda.is_available():

        # TensorFloat-32 행렬 곱셈을 허용하여
        # 지원 GPU에서 연산 속도를 향상시킬 수 있습니다.
        torch.backends.cuda.matmul.allow_tf32 = True

        # cuDNN에서도 TF32 연산을 허용합니다.
        torch.backends.cudnn.allow_tf32 = True

    # 현재 실행 환경을 출력합니다.
    print_environment()

    # 필요한 데이터 파일이 존재하는지 검사합니다.
    validate_files()

    # JSONL 데이터셋을 로드합니다.
    train_dataset, valid_dataset = load_sft_datasets()

    # 모델 Tokenizer를 로드합니다.
    tokenizer = load_tokenizer()

    # GPU 지원 여부에 따라 BF16 또는 FP16을 선택합니다.
    compute_dtype = select_compute_dtype()

    # 사전 학습 모델을 4bit 양자화 상태로 불러옵니다.
    model = load_quantized_model(
        tokenizer=tokenizer,
        compute_dtype=compute_dtype,
    )

    # LoRA Adapter 설정을 생성합니다.
    lora_config = create_lora_config()

    # SFT 학습 설정을 생성합니다.
    training_config = create_training_config(
        compute_dtype=compute_dtype,
    )

    # SFTTrainer를 생성합니다.
    # peft_config를 전달하면 Trainer가 모델에 LoRA Adapter를 적용합니다.
    trainer = SFTTrainer(
        # 학습할 사전 학습 모델입니다.
        model=model,

        # SFT 학습 설정입니다.
        args=training_config,

        # 학습용 대화 데이터셋입니다.
        train_dataset=train_dataset,

        # 검증용 대화 데이터셋입니다.
        eval_dataset=valid_dataset,

        # Tokenizing과 Chat Template 적용에 사용할 Tokenizer입니다.
        processing_class=tokenizer,

        # 모델에 추가할 LoRA Adapter 설정입니다.
        peft_config=lora_config,
    )

    # Trainer가 LoRA를 적용한 이후의 파라미터 개수를 계산합니다.
    parameter_info = count_parameters(trainer.model)

    # 파라미터 정보를 출력합니다.
    print("\n" + "=" * 80)
    print("6. 학습 파라미터 확인")
    print("=" * 80)
    print(
        f"전체 파라미터     : "
        f"{parameter_info['total_parameters']:,}"
    )
    print(
        f"학습 파라미터     : "
        f"{parameter_info['trainable_parameters']:,}"
    )
    print(
        f"학습 파라미터 비율: "
        f"{parameter_info['trainable_ratio']:.4f}%"
    )

    # Trainer가 제공하는 LoRA 파라미터 정보도 출력합니다.
    if hasattr(trainer.model, "print_trainable_parameters"):
        trainer.model.print_trainable_parameters()

    # 학습 시작 정보를 출력합니다.
    print("\n" + "=" * 80)
    print("7. Supervised Fine-Tuning 시작")
    print("=" * 80)

    # 실제 SFT 학습을 실행합니다.
    train_result = trainer.train()

    # 학습 완료 정보를 출력합니다.
    print("\n" + "=" * 80)
    print("8. 학습 완료")
    print("=" * 80)
    print(f"최종 Training Loss : {train_result.training_loss}")

    # 학습 결과 Metric을 딕셔너리로 가져옵니다.
    train_metrics = train_result.metrics

    # 학습 데이터 수를 Metric에 추가합니다.
    train_metrics["train_samples"] = len(train_dataset)

    # 학습 결과를 Trainer 로그로 출력합니다.
    trainer.log_metrics(
        "train",
        train_metrics,
    )

    # 학습 결과를 Trainer 형식으로 저장합니다.
    trainer.save_metrics(
        "train",
        train_metrics,
    )

    # Trainer의 상태를 JSON 파일로 저장합니다.
    trainer.save_state()

    # 검증 데이터로 최종 평가를 수행합니다.
    eval_metrics = trainer.evaluate()

    # 검증 데이터 수를 Metric에 추가합니다.
    eval_metrics["eval_samples"] = len(valid_dataset)

    # 검증 결과를 화면에 출력합니다.
    trainer.log_metrics(
        "eval",
        eval_metrics,
    )

    # 검증 결과를 파일로 저장합니다.
    trainer.save_metrics(
        "eval",
        eval_metrics,
    )

    # 최종 LoRA Adapter를 지정된 출력 경로에 저장합니다.
    trainer.save_model(str(OUTPUT_DIR))

    # Tokenizer도 같은 경로에 저장합니다.
    tokenizer.save_pretrained(str(OUTPUT_DIR))

    # 학습에 사용된 주요 설정을 별도 JSON 파일로 저장합니다.
    save_json(
        {
            "base_model": MODEL_NAME,
            "output_dir": str(OUTPUT_DIR),
            "max_length": MAX_LENGTH,
            "train_batch_size": TRAIN_BATCH_SIZE,
            "eval_batch_size": EVAL_BATCH_SIZE,
            "gradient_accumulation_steps": GRADIENT_ACCUMULATION_STEPS,
            "effective_batch_size": (
                TRAIN_BATCH_SIZE
                * GRADIENT_ACCUMULATION_STEPS
            ),
            "num_train_epochs": NUM_TRAIN_EPOCHS,
            "learning_rate": LEARNING_RATE,
            "weight_decay": WEIGHT_DECAY,
            "warmup_ratio": WARMUP_RATIO,
            "compute_dtype": str(compute_dtype),
            "lora_r": lora_config.r,
            "lora_alpha": lora_config.lora_alpha,
            "lora_dropout": lora_config.lora_dropout,
            "target_modules": list(lora_config.target_modules),
            "parameter_info": parameter_info,
            "train_metrics": train_metrics,
            "eval_metrics": eval_metrics,
        },
        OUTPUT_DIR / "training_summary.json",
    )

    # 학습된 모델로 간단한 질문을 테스트합니다.
    test_question = "배송 완료로 나오지만 상품을 받지 못했습니다."

    # 테스트 질문을 화면에 출력합니다.
    print("\n" + "=" * 80)
    print("9. 학습 모델 추론 테스트")
    print("=" * 80)
    print(f"[질문]\n{test_question}")

    # 모델 답변을 생성합니다.
    test_answer = run_test_inference(
        model=trainer.model,
        tokenizer=tokenizer,
        question=test_question,
    )

    # 생성 결과를 출력합니다.
    print(f"\n[답변]\n{test_answer}")

    # 테스트 결과를 JSON 파일로 저장합니다.
    save_json(
        {
            "question": test_question,
            "answer": test_answer,
        },
        OUTPUT_DIR / "test_generation.json",
    )

    # 최종 저장 경로를 출력합니다.
    print("\n" + "=" * 80)
    print("10. 전체 파이프라인 완료")
    print("=" * 80)
    print(f"LoRA Adapter 저장 위치 : {OUTPUT_DIR}")
    print(
        "다음 명령으로 저장된 Adapter를 불러와 추론할 수 있습니다.\n"
        "python 03_inference.py"
    )

    # Trainer와 모델 객체 참조를 제거합니다.
    del trainer
    del model

    # 사용하지 않는 파이썬 객체를 정리합니다.
    gc.collect()

    # CUDA 캐시 메모리를 해제합니다.
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


# 이 파일을 직접 실행한 경우에만 main 함수를 호출합니다.
if __name__ == "__main__":
    main()
