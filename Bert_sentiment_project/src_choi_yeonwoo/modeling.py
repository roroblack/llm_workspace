"""한국어 분류 모델 생성과 Fine-tuning 범위 설정을 담당하는 파일입니다.

영어용 `src/modeling.py` 와 동일한 함수명을 유지하되, BERT 전용 클래스 대신
AutoModelForSequenceClassification 을 사용해 KoELECTRA/KoBERT 등을 모두 지원합니다.
"""

from transformers import AutoModelForSequenceClassification, PreTrainedModel


def create_model(model_name: str, num_labels: int = 2) -> PreTrainedModel:
    """Hugging Face Hub 또는 로컬 경로에서 문장 분류 모델을 불러옵니다."""
    # AutoModelForSequenceClassification 은 모델 본체 위에 분류 헤드를 붙여 줍니다.
    # 사전학습 백본(분류 헤드 없음)을 불러올 때 헤드 크기가 달라도 새로 초기화되도록 옵션을 둡니다.
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=num_labels,
        ignore_mismatched_sizes=True,
    )

    # 생성한 모델 객체를 반환합니다.
    return model


def apply_fine_tuning_strategy(model: PreTrainedModel, strategy: int = 3) -> PreTrainedModel:
    """전략 값에 따라 백본의 학습 가능 범위를 조정합니다.

    0: 전체 파라미터 학습(풀 파인튜닝) — 정확도가 가장 높지만 가장 느림
    1: 백본 전체 동결(분류 헤드만 학습)
    2: 백본 동결 + (가능하면) pooler 만 학습
    3: 마지막 인코더 레이어 + pooler 만 학습 (기본값)
    """
    # 여러 번 실행해도 이전 설정이 남지 않도록 전체 파라미터를 먼저 학습 가능 상태로 둡니다.
    for param in model.parameters():
        param.requires_grad = True

    # 전략 0은 동결 없이 전체 파라미터를 그대로 학습합니다.
    if strategy == 0:
        return model

    # 모델마다 본체 속성 이름이 달라(electra/bert 등) named_parameters 전체에서 분류 헤드를 제외합니다.
    # 분류 헤드(classifier)는 항상 학습하고, 백본 부분만 전략에 따라 동결합니다.
    backbone_params = [(name, p) for name, p in model.named_parameters() if "classifier" not in name]

    # 백본 안에서 "마지막 인코더 레이어"를 찾기 위해 layer.N 형태의 최대 번호를 계산합니다.
    layer_indices = []
    for name, _ in backbone_params:
        for part in name.split("."):
            if part.isdigit():
                layer_indices.append(int(part))
    last_layer_index = max(layer_indices) if layer_indices else -1
    last_layer_tag = f".{last_layer_index}." if last_layer_index >= 0 else None

    if strategy == 1:
        # 전략 1: 백본 전체 동결, 분류 헤드만 학습합니다.
        for _, param in backbone_params:
            param.requires_grad = False

    elif strategy == 2:
        # 전략 2: pooler 를 제외한 백본 전체를 동결합니다.
        for name, param in backbone_params:
            if "pooler" not in name:
                param.requires_grad = False

    elif strategy == 3:
        # 전략 3: 마지막 인코더 레이어와 pooler 를 제외한 백본을 동결합니다.
        for name, param in backbone_params:
            keep = ("pooler" in name) or (last_layer_tag is not None and last_layer_tag in name)
            if not keep:
                param.requires_grad = False

    else:
        # 허용되지 않는 전략 값이면 즉시 오류를 발생시켜 잘못된 학습 설정을 막습니다.
        raise ValueError("strategy는 1, 2, 3 중 하나여야 합니다.")

    # Fine-tuning 설정이 반영된 모델을 반환합니다.
    return model


def count_trainable_parameters(model: PreTrainedModel) -> dict[str, int]:
    """전체 파라미터 수와 학습 가능한 파라미터 수를 계산합니다."""
    # 모델이 가진 모든 파라미터 원소 개수를 합산합니다.
    total_params = sum(param.numel() for param in model.parameters())

    # requires_grad=True인 파라미터만 학습 가능한 파라미터로 계산합니다.
    trainable_params = sum(param.numel() for param in model.parameters() if param.requires_grad)

    # 계산 결과를 딕셔너리 형태로 반환합니다.
    return {
        "total_params": total_params,
        "trainable_params": trainable_params,
        "frozen_params": total_params - trainable_params,
    }
