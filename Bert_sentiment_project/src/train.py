"""BERT 감성분석 모델을 학습하고 저장하는 실행 파일입니다."""

import argparse

import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from transformers import BertTokenizerFast, Trainer, TrainingArguments

from src.config import DEFAULT_DATA_PATH, DEFAULT_MODEL_NAME, MAX_LEN, MODEL_DIR, SEED
from src.data_loader import load_sentiment_csv, split_dataset
from src.dataset import BertSentimentDataset
from src.modeling import apply_fine_tuning_strategy, count_trainable_parameters, create_model
from src.utils import get_device, set_seed


def compute_metrics(pred) -> dict[str, float]:
    """Trainer 평가 결과에서 정확도, 정밀도, 재현율, F1-score를 계산합니다."""
    # 실제 정답 라벨 배열을 가져옵니다.
    labels = pred.label_ids

    # 모델 출력 로짓에서 가장 큰 값을 가진 클래스 인덱스를 예측 라벨로 사용합니다.
    predictions = np.argmax(pred.predictions, axis=-1)

    # 전체 샘플 중 정답을 맞힌 비율인 정확도를 계산합니다.
    accuracy = accuracy_score(labels, predictions)

    # 이진 분류 기준의 정밀도, 재현율, F1-score를 계산합니다.
    precision, recall, f1, _ = precision_recall_fscore_support(labels, predictions, average="binary", zero_division=0)

    # Trainer가 로그로 출력할 수 있도록 딕셔너리 형태로 반환합니다.
    return {"accuracy": accuracy, "precision": precision, "recall": recall, "f1": f1}


def train(args: argparse.Namespace) -> None:
    """명령행 인자를 받아 데이터 로드부터 모델 저장까지 전체 학습을 수행합니다."""
    # 학습 결과가 최대한 재현되도록 난수 시드를 고정합니다.
    set_seed(SEED)

    # GPU가 있으면 GPU를 사용하고, 없으면 CPU를 사용합니다.
    device = get_device()

    # CSV 파일을 읽고 라벨을 숫자로 변환합니다.
    dataset = load_sentiment_csv(args.data_path)

    # 데이터를 학습, 검증, 테스트 세트로 나눕니다.
    train_df, valid_df, test_df = split_dataset(dataset)

    # 학습에 사용할 토크나이저를 다운로드하거나 캐시에서 불러옵니다.
    tokenizer = BertTokenizerFast.from_pretrained(args.model_name)

    # DataFrame을 Trainer가 사용할 수 있는 PyTorch Dataset 객체로 변환합니다.
    train_dataset = BertSentimentDataset(train_df["review"], train_df["sentiment"], tokenizer, max_len=args.max_len)

    # 검증 데이터도 같은 토크나이저와 최대 길이로 Dataset 객체를 만듭니다.
    valid_dataset = BertSentimentDataset(valid_df["review"], valid_df["sentiment"], tokenizer, max_len=args.max_len)

    # 최종 평가를 위해 테스트 Dataset 객체도 준비합니다.
    test_dataset = BertSentimentDataset(test_df["review"], test_df["sentiment"], tokenizer, max_len=args.max_len)

    # BERT 문장 분류 모델을 생성합니다.
    model = create_model(args.model_name, num_labels=2)

    # 선택한 Fine-tuning 전략에 따라 학습할 파라미터 범위를 조정합니다.
    model = apply_fine_tuning_strategy(model, strategy=args.strategy)

    # 모델을 GPU 또는 CPU 장치로 이동합니다.
    model.to(device)

    # 전체 파라미터와 학습 가능한 파라미터 수를 출력합니다.
    print("파라미터 정보:", count_trainable_parameters(model))

    # 학습 결과와 체크포인트를 저장할 경로를 문자열로 변환합니다.
    output_dir = str(args.output_dir)

    # Trainer 학습 옵션을 정의합니다.
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.train_batch_size,
        per_device_eval_batch_size=args.eval_batch_size,
        warmup_steps=args.warmup_steps,
        weight_decay=args.weight_decay,
        save_strategy="epoch",
        eval_strategy="epoch",
        logging_steps=10,
        report_to="none",
        seed=SEED,
    )

    # Hugging Face Trainer 객체를 생성합니다.
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=valid_dataset,
        compute_metrics=compute_metrics,
    )

    # 모델 Fine-tuning 학습을 실행합니다.
    trainer.train()

    # 테스트 데이터로 최종 평가를 수행합니다.
    test_result = trainer.predict(test_dataset)

    # 테스트 평가 지표를 출력합니다.
    print("테스트 평가 결과:", test_result.metrics)

    # Streamlit 앱에서 바로 불러올 수 있도록 모델을 저장합니다.
    trainer.save_model(output_dir)

    # 모델과 반드시 같은 토크나이저를 저장합니다.
    tokenizer.save_pretrained(output_dir)

    # 저장 완료 메시지를 출력합니다.
    print(f"모델 저장 완료: {output_dir}")


def parse_args() -> argparse.Namespace:
    """명령행 인자를 정의하고 파싱합니다."""
    # argparse는 터미널 실행 옵션을 처리하기 위한 표준 라이브러리입니다.
    parser = argparse.ArgumentParser(description="BERT 감성분석 모델 학습 스크립트")

    # 학습 CSV 파일 경로를 입력받습니다.
    parser.add_argument("--data_path", type=str, default=str(DEFAULT_DATA_PATH), help="review,sentiment 컬럼을 가진 CSV 파일 경로")

    # 사용할 사전 학습 BERT 모델명을 입력받습니다.
    parser.add_argument("--model_name", type=str, default=DEFAULT_MODEL_NAME, help="Hugging Face BERT 모델명")

    # 학습된 모델 저장 경로를 입력받습니다.
    parser.add_argument("--output_dir", type=str, default=str(MODEL_DIR), help="학습 모델 저장 폴더")

    # 입력 문장의 최대 토큰 길이를 입력받습니다.
    parser.add_argument("--max_len", type=int, default=MAX_LEN, help="BERT 최대 입력 토큰 길이")

    # Fine-tuning 전략을 입력받습니다.
    parser.add_argument("--strategy", type=int, default=3, choices=[1, 2, 3], help="Fine-tuning 전략 번호")

    # 학습 epoch 수를 입력받습니다.
    parser.add_argument("--epochs", type=int, default=1, help="학습 반복 횟수")

    # 학습 배치 크기를 입력받습니다.
    parser.add_argument("--train_batch_size", type=int, default=8, help="학습 배치 크기")

    # 평가 배치 크기를 입력받습니다.
    parser.add_argument("--eval_batch_size", type=int, default=16, help="평가 배치 크기")

    # warmup step 수를 입력받습니다.
    parser.add_argument("--warmup_steps", type=int, default=0, help="학습률 warmup step 수")

    # weight decay 값을 입력받습니다.
    parser.add_argument("--weight_decay", type=float, default=0.01, help="가중치 감쇠 정규화 강도")

    # 파싱한 인자 객체를 반환합니다.
    return parser.parse_args()


if __name__ == "__main__":
    # 이 파일을 직접 실행할 때만 명령행 인자를 읽고 학습을 시작합니다.
    train(parse_args())
