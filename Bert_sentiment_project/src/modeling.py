"""BERT 분류 모델 생성과 Fine-tuning 범위 설정을 담당하는 파일입니다."""

from transformers import BertForSequenceClassification


def create_model(model_name: str, num_labels: int = 2) -> BertForSequenceClassification:
    """Hugging Face Hub 또는 로컬 경로에서 BERT 문장 분류 모델을 불러옵니다."""
    # BertForSequenceClassification은 BERT 본체 위에 분류용 Linear Layer가 붙은 모델입니다.
    model = BertForSequenceClassification.from_pretrained(model_name, num_labels=num_labels)

    # 생성한 모델 객체를 반환합니다.
    return model


def apply_fine_tuning_strategy(model: BertForSequenceClassification, strategy: int = 3) -> BertForSequenceClassification:
    """전략 값에 따라 BERT 본체의 학습 가능 범위를 조정합니다."""
    # 여러 번 실행해도 이전 설정이 남지 않도록 전체 파라미터를 먼저 학습 가능 상태로 초기화합니다.
    for param in model.parameters():
        param.requires_grad = True

    # BERT Base 모델의 마지막 Encoder Layer 이름입니다.
    last_encoder_layer_name = "encoder.layer.11"

    if strategy == 1:
        # 전략 1은 BERT 본체 전체를 동결하고 classifier만 학습합니다.
        for name, param in model.bert.named_parameters():
            param.requires_grad = False

    elif strategy == 2:
        # 전략 2는 BERT 본체 중 pooler만 학습하고 나머지 본체를 동결합니다.
        for name, param in model.bert.named_parameters():
            if not name.startswith("pooler"):
                param.requires_grad = False

    elif strategy == 3:
        # 전략 3은 마지막 Encoder Layer와 pooler만 학습하고 나머지 BERT 본체를 동결합니다.
        for name, param in model.bert.named_parameters():
            if (not name.startswith("pooler")) and (last_encoder_layer_name not in name):
                param.requires_grad = False

    else:
        # 허용되지 않는 전략 값이면 즉시 오류를 발생시켜 잘못된 학습 설정을 막습니다.
        raise ValueError("strategy는 1, 2, 3 중 하나여야 합니다.")

    # Fine-tuning 설정이 반영된 모델을 반환합니다.
    return model


def count_trainable_parameters(model: BertForSequenceClassification) -> dict[str, int]:
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
