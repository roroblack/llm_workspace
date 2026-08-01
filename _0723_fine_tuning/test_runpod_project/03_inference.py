"""
학습이 완료된 LoRA Adapter를 불러와
사용자 질문에 대한 답변을 생성하는 코드입니다.
"""

# os 모듈은 환경변수를 읽을 때 사용합니다.
import os

# Path는 파일과 디렉터리 경로를 처리합니다.
from pathlib import Path

# PyTorch는 GPU 연산과 Tensor 처리를 담당합니다.
import torch

# .env 파일의 환경변수를 불러옵니다.
from dotenv import load_dotenv

# 사전 학습 모델, Tokenizer 및 양자화 설정을 불러옵니다.
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)

# 기본 모델에 학습된 LoRA Adapter를 연결하기 위해 사용합니다.
from peft import PeftModel


# 현재 파일의 위치를 프로젝트 기준 디렉터리로 지정합니다.
BASE_DIR = Path(__file__).resolve().parent

# .env 환경변수를 읽습니다.
load_dotenv(BASE_DIR / ".env")

# 학습에 사용한 기본 모델 이름을 가져옵니다.
BASE_MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "Qwen/Qwen2.5-0.5B-Instruct",
)

# 학습된 LoRA Adapter 디렉터리를 설정합니다.
ADAPTER_DIR = BASE_DIR / os.getenv(
    "OUTPUT_DIR",
    "outputs/qwen2.5-korean-sft-lora",
)

# Hugging Face 접근 토큰을 읽습니다.
HF_TOKEN = os.getenv("HF_TOKEN") or None


def select_compute_dtype() -> torch.dtype:
    """
    GPU가 BF16을 지원하면 BF16을 사용하고,
    그렇지 않으면 FP16을 사용합니다.
    """

    # CUDA GPU가 BF16을 지원하는지 확인합니다.
    if (
        torch.cuda.is_available()
        and torch.cuda.is_bf16_supported()
    ):
        return torch.bfloat16

    # BF16을 지원하지 않으면 FP16을 반환합니다.
    return torch.float16


def load_model_and_tokenizer():
    """
    기본 모델과 학습된 LoRA Adapter 및 Tokenizer를 불러옵니다.

    Returns:
        model: Adapter가 연결된 추론 모델
        tokenizer: 학습 시 저장한 Tokenizer
    """

    # 학습된 Adapter 디렉터리가 존재하는지 검사합니다.
    if not ADAPTER_DIR.exists():
        raise FileNotFoundError(
            f"LoRA Adapter를 찾을 수 없습니다: {ADAPTER_DIR}\n"
            "먼저 python 02_train_sft.py를 실행하세요."
        )

    # GPU 연산에 사용할 데이터 타입을 선택합니다.
    compute_dtype = select_compute_dtype()

    # 4bit 양자화 설정을 생성합니다.
    quantization_config = BitsAndBytesConfig(

        # 기본 모델을 4bit 상태로 로드합니다.
        load_in_4bit=True,

        # NF4 양자화 방식을 사용합니다.
        bnb_4bit_quant_type="nf4",

        # 이중 양자화를 적용합니다.
        bnb_4bit_use_double_quant=True,

        # 실제 계산은 BF16 또는 FP16으로 수행합니다.
        bnb_4bit_compute_dtype=compute_dtype,
    )

    # 학습할 때 저장한 Tokenizer를 Adapter 경로에서 불러옵니다.
    tokenizer = AutoTokenizer.from_pretrained(
        str(ADAPTER_DIR),
        trust_remote_code=True,
    )

    # Padding Token이 없으면 EOS Token을 사용합니다.
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 기본 사전 학습 모델을 4bit로 불러옵니다.
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_NAME,
        quantization_config=quantization_config,
        device_map={"": 0},
        trust_remote_code=True,
        token=HF_TOKEN,
    )

    # 기본 모델의 Padding Token ID를 설정합니다.
    base_model.config.pad_token_id = tokenizer.pad_token_id

    # 기본 모델 위에 학습된 LoRA Adapter를 연결합니다.
    model = PeftModel.from_pretrained(
        base_model,
        str(ADAPTER_DIR),
    )

    # 추론 속도 향상을 위해 KV Cache를 활성화합니다.
    model.config.use_cache = True

    # 모델을 평가 모드로 변경합니다.
    model.eval()

    # 완성된 모델과 Tokenizer를 반환합니다.
    return model, tokenizer


def generate_answer(
    model,
    tokenizer,
    question: str,
) -> str:
    """
    사용자 질문을 모델에 입력하여 답변을 생성합니다.

    Args:
        model: LoRA Adapter가 적용된 모델
        tokenizer: 모델 Tokenizer
        question: 사용자가 입력한 질문

    Returns:
        생성된 답변 문자열
    """

    # 모델에게 전달할 대화 메시지를 구성합니다.
    messages = [
        {
            "role": "system",
            "content": (
                "당신은 온라인 쇼핑몰의 고객 상담 AI입니다. "
                "고객의 질문을 정확히 이해하고 친절하게 답변하세요. "
                "확인되지 않은 사실은 임의로 만들지 마세요."
            ),
        },
        {
            "role": "user",
            "content": question,
        },
    ]

    # Qwen 모델의 Chat Template을 적용합니다.
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    # 프롬프트를 Token ID와 Attention Mask로 변환합니다.
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
    )

    # 입력 데이터를 모델이 위치한 GPU로 이동합니다.
    inputs = {
        key: value.to(model.device)
        for key, value in inputs.items()
    }

    # Gradient 계산이 필요하지 않은 추론 모드로 실행합니다.
    with torch.inference_mode():

        # 모델 답변 토큰을 생성합니다.
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=256,
            do_sample=True,
            temperature=0.6,
            top_p=0.9,
            repetition_penalty=1.1,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    # 입력 프롬프트 부분을 제외한 신규 생성 토큰만 추출합니다.
    generated_tokens = generated_ids[
        :,
        inputs["input_ids"].shape[1]:
    ]

    # 생성된 토큰을 문자열로 변환합니다.
    answer = tokenizer.batch_decode(
        generated_tokens,
        skip_special_tokens=True,
    )[0]

    # 답변의 앞뒤 공백을 제거하여 반환합니다.
    return answer.strip()


def main() -> None:
    """
    모델을 한 번 로드한 후 사용자의 질문을 반복해서 처리합니다.
    """

    # 프로그램 제목을 출력합니다.
    print("=" * 70)
    print("Qwen2.5 한국어 고객 상담 SFT 모델")
    print("=" * 70)

    # 기본 모델과 LoRA Adapter 및 Tokenizer를 불러옵니다.
    model, tokenizer = load_model_and_tokenizer()

    # 모델 로드 완료 메시지를 출력합니다.
    print("모델과 LoRA Adapter 로드가 완료되었습니다.")
    print("'종료', 'exit' 또는 'quit'을 입력하면 종료됩니다.")

    # 사용자가 종료 명령을 입력할 때까지 반복합니다.
    while True:

        # 사용자 질문을 입력받습니다.
        question = input("\n질문: ").strip()

        # 종료 명령어 목록에 포함되면 반복을 종료합니다.
        if question.lower() in {
            "종료",
            "exit",
            "quit",
        }:
            print("프로그램을 종료합니다.")
            break

        # 아무 내용도 입력하지 않은 경우 다시 입력받습니다.
        if not question:
            print("질문을 입력해 주세요.")
            continue

        # 모델을 사용해 답변을 생성합니다.
        answer = generate_answer(
            model=model,
            tokenizer=tokenizer,
            question=question,
        )

        # 생성된 답변을 출력합니다.
        print(f"\n답변: {answer}")


# 이 파일을 직접 실행한 경우 main 함수를 호출합니다.
if __name__ == "__main__":
    main()
