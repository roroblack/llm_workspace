"""CSV 감성분석 데이터를 읽고 BERT 학습에 맞는 형태로 정리하는 파일입니다."""

from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from src.config import LABEL_TO_ID, SEED


def load_sentiment_csv(data_path: str | Path) -> pd.DataFrame:
    """review, sentiment 컬럼을 가진 CSV 파일을 읽어 정제된 DataFrame으로 반환합니다."""
    # 문자열 경로나 Path 객체를 모두 처리할 수 있도록 Path 객체로 변환합니다.
    data_path = Path(data_path)

    # 데이터 파일이 없으면 사용자가 경로를 수정할 수 있도록 명확한 예외를 발생시킵니다.
    if not data_path.exists():
        raise FileNotFoundError(f"데이터 파일을 찾을 수 없습니다: {data_path}")

    # UTF-8 CSV를 우선 읽습니다. 대부분의 공개 데이터셋은 UTF-8 형식을 사용합니다.
    try:
        dataset = pd.read_csv(data_path)
    except UnicodeDecodeError:
        # Windows에서 저장한 한글 CSV는 cp949 인코딩일 수 있으므로 실패 시 cp949로 다시 읽습니다.
        dataset = pd.read_csv(data_path, encoding="cp949")

    # 컬럼명 앞뒤 공백을 제거하여 " review " 같은 문제를 예방합니다.
    dataset.columns = dataset.columns.str.strip()

    # 학습에 필요한 review 컬럼과 sentiment 컬럼이 있는지 확인합니다.
    required_columns = {"review", "sentiment"}
    if not required_columns.issubset(set(dataset.columns)):
        raise ValueError("CSV 파일에는 review, sentiment 컬럼이 반드시 있어야 합니다.")

    # 리뷰 또는 라벨이 비어 있는 행은 학습 오류를 막기 위해 제거합니다.
    dataset = dataset.dropna(subset=["review", "sentiment"]).reset_index(drop=True)

    # sentiment 값을 positive/negative 또는 긍정/부정 문자열에서 1/0 숫자 라벨로 변환합니다.
    dataset["sentiment"] = dataset["sentiment"].map(lambda value: LABEL_TO_ID.get(value, LABEL_TO_ID.get(str(value).strip().lower())))

    # 변환되지 않은 라벨이 있으면 학습 전에 데이터 오류를 알려줍니다.
    if dataset["sentiment"].isna().any():
        raise ValueError("sentiment 컬럼은 positive/negative, 긍정/부정, 1/0 중 하나로 작성해야 합니다.")

    # Trainer가 요구하는 정수 라벨 형식으로 변환합니다.
    dataset["sentiment"] = dataset["sentiment"].astype(int)

    # review 컬럼을 문자열로 변환하여 숫자나 결측 혼합 데이터로 인한 토큰화 오류를 줄입니다.
    dataset["review"] = dataset["review"].astype(str)

    # 정제된 데이터프레임을 반환합니다.
    return dataset


def split_dataset(dataset: pd.DataFrame):
    """전체 데이터를 train, validation, test 세트로 분리합니다."""
    # 전체 데이터를 먼저 학습용 80%, 테스트용 20%로 나눕니다.
    train_df, test_df = train_test_split(
        dataset,
        test_size=0.2,
        stratify=dataset["sentiment"],
        random_state=SEED,
    )

    # 학습용 데이터에서 다시 검증용 30%를 분리합니다.
    train_df, valid_df = train_test_split(
        train_df,
        test_size=0.3,
        stratify=train_df["sentiment"],
        random_state=SEED,
    )

    # 인덱스를 0부터 다시 정리하여 Dataset 접근을 단순하게 만듭니다.
    return train_df.reset_index(drop=True), valid_df.reset_index(drop=True), test_df.reset_index(drop=True)
