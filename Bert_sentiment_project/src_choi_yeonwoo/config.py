"""한국어 감성분석 패키지 전체에서 사용하는 경로와 기본 설정을 모아 둔 파일입니다.

영어용 `src/config.py` 와 동일한 역할을 하지만, 기본 모델을 한국어 감성분석 모델로
바꾸고 NSMC(Naver sentiment movie corpus) 데이터 경로를 추가했습니다.
"""

from pathlib import Path

# 현재 파일(config.py)의 위치를 기준으로 프로젝트 루트 경로를 계산합니다.
BASE_DIR = Path(__file__).resolve().parents[1]

# CSV/TSV 데이터 파일이 저장되는 기본 폴더 경로입니다.
DATA_DIR = BASE_DIR / "data"

# 직접 파인튜닝한 한국어 모델과 토크나이저가 저장되는 폴더 경로입니다.
MODEL_DIR = BASE_DIR / "models" / "korean_sentiment"

# 한국어 감성분석에 바로 사용할 수 있는 사전학습(NSMC fine-tuned) 모델명입니다.
# KoELECTRA 를 NSMC(영화 리뷰 긍정/부정)로 미세조정한 공개 모델로, 학습 없이 즉시 사용 가능합니다.
DEFAULT_MODEL_NAME = "monologg/koelectra-base-finetuned-nsmc"

# 직접 파인튜닝(train.py) 할 때 사용할 한국어 사전학습 백본 모델명입니다.
# NAVER 뉴스 분류 작업물에서 쓰던 KoELECTRA discriminator 를 그대로 사용합니다.
BASE_MODEL_NAME = "monologg/koelectra-base-v3-discriminator"

# NSMC 원본 데이터(탭 구분 TSV) 경로입니다. train.py 가 없으면 자동으로 내려받습니다.
NSMC_TRAIN_PATH = DATA_DIR / "nsmc_ratings_train.txt"
NSMC_TEST_PATH = DATA_DIR / "nsmc_ratings_test.txt"

# NSMC 원본 데이터를 내려받을 공개 URL 입니다.
NSMC_TRAIN_URL = "https://raw.githubusercontent.com/e9t/nsmc/master/ratings_train.txt"
NSMC_TEST_URL = "https://raw.githubusercontent.com/e9t/nsmc/master/ratings_test.txt"

# 모델 입력에 사용할 최대 토큰 길이입니다. 영화 리뷰는 짧아 64면 충분합니다.
MAX_LEN = 64

# 학습과 데이터 분리에 사용할 난수 시드입니다.
SEED = 42

# 숫자 라벨을 화면 표시용 문자열로 바꾸기 위한 딕셔너리입니다. (NSMC: 0=부정, 1=긍정)
ID_TO_LABEL = {0: "부정", 1: "긍정"}

# 문자열/숫자 라벨을 학습용 숫자 라벨로 바꾸기 위한 딕셔너리입니다.
LABEL_TO_ID = {"negative": 0, "부정": 0, "0": 0, 0: 0, "positive": 1, "긍정": 1, "1": 1, 1: 1}
