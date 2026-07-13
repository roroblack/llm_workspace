"""한국어 감성분석 데이터를 읽고 모델 학습에 맞는 형태로 정리하는 파일입니다.

영어용 `src/data_loader.py` 와 같은 함수명(load_sentiment_csv, split_dataset)을 유지하면서,
NSMC(Naver sentiment movie corpus) TSV 데이터를 내려받아 사용할 수 있도록 확장했습니다.
"""

import urllib.request
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from src_choi_yeonwoo.config import (
    LABEL_TO_ID,
    NSMC_TEST_PATH,
    NSMC_TEST_URL,
    NSMC_TRAIN_PATH,
    NSMC_TRAIN_URL,
    SEED,
)


def download_nsmc_if_needed() -> tuple[Path, Path]:
    """NSMC 원본 TSV(train/test)가 없으면 공개 저장소에서 내려받습니다."""
    # 데이터 폴더가 없으면 먼저 생성합니다.
    NSMC_TRAIN_PATH.parent.mkdir(parents=True, exist_ok=True)

    # (로컬 경로, 원격 URL) 쌍을 순회하며 없는 파일만 내려받습니다.
    for local_path, url in ((NSMC_TRAIN_PATH, NSMC_TRAIN_URL), (NSMC_TEST_PATH, NSMC_TEST_URL)):
        if not local_path.exists():
            print(f"NSMC 데이터 다운로드: {url}")
            urllib.request.urlretrieve(url, local_path)

    # 내려받은(또는 이미 있던) 파일 경로를 반환합니다.
    return NSMC_TRAIN_PATH, NSMC_TEST_PATH


def load_nsmc(path: str | Path) -> pd.DataFrame:
    """NSMC TSV 파일(id, document, label)을 읽어 review/sentiment DataFrame으로 반환합니다."""
    # NSMC는 탭으로 구분된 TSV 형식입니다.
    dataset = pd.read_csv(path, sep="\t")

    # 학습에 사용할 컬럼만 표준 컬럼명(review, sentiment)으로 바꿉니다.
    dataset = dataset.rename(columns={"document": "review", "label": "sentiment"})

    # 본문이 비어 있는 행은 토큰화 오류를 막기 위해 제거합니다.
    dataset = dataset.dropna(subset=["review", "sentiment"]).reset_index(drop=True)

    # 리뷰는 문자열, 라벨은 정수로 정리합니다. (NSMC: 0=부정, 1=긍정)
    dataset["review"] = dataset["review"].astype(str)
    dataset["sentiment"] = dataset["sentiment"].astype(int)

    # 정제된 데이터프레임을 반환합니다.
    return dataset[["review", "sentiment"]]


def load_sentiment_csv(data_path: str | Path) -> pd.DataFrame:
    """review, sentiment 컬럼을 가진 CSV 파일을 읽어 정제된 DataFrame으로 반환합니다.

    영어용 src/data_loader.py 와 동일한 규칙으로, 한국어/영어 CSV 모두 지원합니다.
    """
    # 문자열 경로나 Path 객체를 모두 처리할 수 있도록 Path 객체로 변환합니다.
    data_path = Path(data_path)

    # 데이터 파일이 없으면 사용자가 경로를 수정할 수 있도록 명확한 예외를 발생시킵니다.
    if not data_path.exists():
        raise FileNotFoundError(f"데이터 파일을 찾을 수 없습니다: {data_path}")

    # UTF-8 CSV를 우선 읽고, 실패하면 한글 Windows에서 흔한 cp949로 다시 읽습니다.
    try:
        dataset = pd.read_csv(data_path)
    except UnicodeDecodeError:
        dataset = pd.read_csv(data_path, encoding="cp949")

    # 컬럼명 앞뒤 공백을 제거합니다.
    dataset.columns = dataset.columns.str.strip()

    # 학습에 필요한 review, sentiment 컬럼이 있는지 확인합니다.
    required_columns = {"review", "sentiment"}
    if not required_columns.issubset(set(dataset.columns)):
        raise ValueError("CSV 파일에는 review, sentiment 컬럼이 반드시 있어야 합니다.")

    # 리뷰 또는 라벨이 비어 있는 행은 제거합니다.
    dataset = dataset.dropna(subset=["review", "sentiment"]).reset_index(drop=True)

    # sentiment 값을 긍정/부정 또는 positive/negative 문자열에서 1/0 숫자 라벨로 변환합니다.
    dataset["sentiment"] = dataset["sentiment"].map(
        lambda value: LABEL_TO_ID.get(value, LABEL_TO_ID.get(str(value).strip().lower()))
    )

    # 변환되지 않은 라벨이 있으면 학습 전에 데이터 오류를 알려줍니다.
    if dataset["sentiment"].isna().any():
        raise ValueError("sentiment 컬럼은 positive/negative, 긍정/부정, 1/0 중 하나로 작성해야 합니다.")

    # 정수 라벨/문자열 리뷰로 정리합니다.
    dataset["sentiment"] = dataset["sentiment"].astype(int)
    dataset["review"] = dataset["review"].astype(str)

    # 정제된 데이터프레임을 반환합니다.
    return dataset[["review", "sentiment"]]


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
