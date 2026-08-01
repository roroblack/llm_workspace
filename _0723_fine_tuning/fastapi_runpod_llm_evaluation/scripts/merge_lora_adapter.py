"""
LoRA 또는 QLoRA Adapter를 기반 모델에 병합하여 독립 모델로 저장합니다.
"""

# 명령행 인자를 읽기 위해 argparse를 가져옵니다.
import argparse

# 출력 경로 생성을 위해 Path를 가져옵니다.
from pathlib import Path


def parse_args() -> argparse.Namespace:
    """
    기반 모델, Adapter, 출력 경로를 명령행에서 읽습니다.
    """

    # 명령행 파서를 생성합니다.
    parser = argparse.ArgumentParser(
        description="PEFT LoRA Adapter 병합"
    )

    # Adapter 학습에 사용한 기반 모델 이름 또는 경로를 받습니다.
    parser.add_argument(
        "--base-model",
        required=True,
    )

    # 학습 완료된 Adapter 디렉터리 경로를 받습니다.
    parser.add_argument(
        "--adapter-path",
        type=Path,
        required=True,
    )

    # 병합 모델을 저장할 출력 경로를 받습니다.
    parser.add_argument(
        "--output-path",
        type=Path,
        required=True,
    )

    # float16 또는 bfloat16 병합 자료형을 선택합니다.
    parser.add_argument(
        "--dtype",
        choices=["float16", "bfloat16"],
        default="bfloat16",
    )

    # 완성된 명령행 인자를 반환합니다.
    return parser.parse_args()


def main() -> None:
    """
    Base 모델을 16비트로 불러온 뒤 Adapter를 병합하고 저장합니다.
    """

    # 명령행 인자를 읽습니다.
    args = parse_args()

    # Adapter 디렉터리가 존재하는지 확인합니다.
    if not args.adapter_path.exists():
        raise FileNotFoundError(
            f"Adapter 디렉터리가 없습니다: {args.adapter_path}"
        )

    # 실제 모델 처리를 위해 PyTorch를 가져옵니다.
    import torch

    # PEFT Adapter 로딩 클래스를 가져옵니다.
    from peft import PeftModel

    # 기반 모델과 토크나이저 클래스를 가져옵니다.
    from transformers import AutoModelForCausalLM, AutoTokenizer

    # 문자열 자료형 선택을 실제 PyTorch dtype으로 변환합니다.
    torch_dtype = (
        torch.float16
        if args.dtype == "float16"
        else torch.bfloat16
    )

    # 병합 시에는 양자화 모델이 아니라 16비트 기반 모델을 불러옵니다.
    base_model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch_dtype,
        device_map="cpu",
        trust_remote_code=True,
    )

    # 기반 모델에 학습된 Adapter를 연결합니다.
    peft_model = PeftModel.from_pretrained(
        base_model,
        str(args.adapter_path),
    )

    # LoRA 가중치를 기반 모델 가중치에 병합하고 PEFT 래퍼를 제거합니다.
    merged_model = peft_model.merge_and_unload()

    # 출력 디렉터리를 생성합니다.
    args.output_path.mkdir(parents=True, exist_ok=True)

    # 병합된 독립 모델을 safetensors 형식으로 저장합니다.
    merged_model.save_pretrained(
        str(args.output_path),
        safe_serialization=True,
    )

    # 기반 모델의 토크나이저를 불러옵니다.
    tokenizer = AutoTokenizer.from_pretrained(
        args.base_model,
        trust_remote_code=True,
    )

    # 토크나이저도 같은 출력 디렉터리에 저장합니다.
    tokenizer.save_pretrained(str(args.output_path))

    # 최종 저장 위치를 출력합니다.
    print(f"병합 모델 저장 완료: {args.output_path}")


# 직접 실행한 경우에만 병합을 수행합니다.
if __name__ == "__main__":
    main()
