"""프로젝트 전체에서 공통으로 사용하는 설정값을 관리하는 파일입니다."""

from pathlib import Path

# 현재 config.py 파일의 상위 폴더(src)의 상위 폴더를 프로젝트 루트로 지정합니다.
BASE_DIR = Path(__file__).resolve().parent.parent

# 학습 데이터 CSV 파일 경로입니다.
DATA_PATH = BASE_DIR / "data" / "translation_pairs.csv"

# 학습된 PyTorch 모델 파일이 저장될 경로입니다.
MODEL_PATH = BASE_DIR / "models" / "smart_translator.pt"

# 문자 사전, 모델 구조, 하이퍼파라미터 등 메타 정보를 함께 저장할 경로입니다.
META_PATH = BASE_DIR / "models" / "translator_meta.pt"

# [변경 요약] Seq2Seq 시절 하이퍼파라미터(EMBED_SIZE=64, HIDDEN_SIZE=128 등 RNN 관련)를
# 아래 Transformer 전용 값(D_MODEL/NHEAD/레이어 수/FFN 차원 등)으로 교체했습니다.

# [신규] 저장된 체크포인트가 현재 Transformer 구현인지 확인하기 위한 식별자입니다.
# 예전 Seq2Seq .pt 파일을 실수로 로딩하는 것을 막는 안전장치입니다.
MODEL_TYPE = "char_transformer"

# Transformer 임베딩/내부 표현 차원입니다. nhead로 나누어떨어져야 합니다.
D_MODEL = 64

# Multi-Head Attention의 head 개수입니다.
NHEAD = 4

# Transformer encoder와 decoder layer 수입니다.
NUM_ENCODER_LAYERS = 1
NUM_DECODER_LAYERS = 1

# 각 Transformer block 내부 Feed Forward Network 차원입니다.
DIM_FEEDFORWARD = 128

# 작은 실습 데이터에 과도한 노이즈를 주지 않도록 dropout은 낮게 둡니다.
DROPOUT = 0.0

# positional embedding이 처리할 수 있는 최대 입력/출력 길이입니다.
MAX_SEQ_LEN = 128

# 학습 반복 횟수입니다. 작은 문자 단위 데이터셋이므로 충분히 반복해 패턴을 익히게 합니다.
EPOCHS = 150

# 한 번에 학습할 데이터 묶음 크기입니다.
BATCH_SIZE = 32

# Transformer 학습용 학습률입니다.
LEARNING_RATE = 0.002

# 번역 결과를 생성할 때 최대 몇 글자까지 만들지 결정합니다.
MAX_OUTPUT_LEN = 80

# 특수 토큰입니다.
PAD_TOKEN = "<PAD>"
SOS_TOKEN = "<SOS>"
EOS_TOKEN = "<EOS>"
UNK_TOKEN = "<UNK>"
