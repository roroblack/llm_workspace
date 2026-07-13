"""프로젝트 전체에서 사용하는 경로와 기본 설정을 모아 둔 파일입니다."""

from pathlib import Path

# 현재 파일(config.py)의 위치를 기준으로 프로젝트 루트 경로를 계산합니다.
BASE_DIR = Path(__file__).resolve().parents[1]

# CSV 데이터 파일이 저장되는 기본 폴더 경로입니다.
DATA_DIR = BASE_DIR / "data"

# 학습된 모델과 토크나이저가 저장되는 기본 폴더 경로입니다.
MODEL_DIR = BASE_DIR / "models" / "bert_sentiment"

# 예제 데이터 경로입니다. 사용자가 별도 데이터를 준비하지 않아도 학습 테스트가 가능합니다.
DEFAULT_DATA_PATH = DATA_DIR / "sample_sentiment.csv"

# Hugging Face에서 내려받을 기본 BERT 모델명입니다.
# 제공된 노트북의 기본값인 bert-base-uncased를 사용합니다.
DEFAULT_MODEL_NAME = "bert-base-uncased"

# BERT 입력에 사용할 최대 토큰 길이입니다.
# 긴 문장은 잘리고 짧은 문장은 padding으로 채워집니다.
MAX_LEN = 128

# 학습과 데이터 분리에 사용할 난수 시드입니다.
SEED = 42

# 숫자 라벨을 화면 표시용 문자열로 바꾸기 위한 딕셔너리입니다.
ID_TO_LABEL = {0: "부정", 1: "긍정"}

# 문자열 라벨을 학습용 숫자 라벨로 바꾸기 위한 딕셔너리입니다.
LABEL_TO_ID = {"negative": 0, "부정": 0, "0": 0, 0: 0, "positive": 1, "긍정": 1, "1": 1, 1: 1}
