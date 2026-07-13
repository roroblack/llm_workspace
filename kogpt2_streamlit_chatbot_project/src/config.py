"""
KoGPT2 챗봇 프로젝트에서 공통으로 사용하는 설정값을 모아 둔 파일입니다.

이 파일을 따로 두면 모델 이름, 생성 길이, 샘플링 옵션 등을 여러 코드 파일에서
중복 작성하지 않고 한 곳에서 관리할 수 있습니다.
"""

# Hugging Face Hub에서 불러올 KoGPT2 모델 이름입니다.
# 노트북에서 사용한 모델과 동일하게 skt/kogpt2-base-v2를 사용합니다.
MODEL_NAME = "skt/kogpt2-base-v2"

# 챗봇이 한 번 답변할 때 새로 생성할 최대 토큰 수입니다.
# 값이 너무 작으면 답변이 짧고, 너무 크면 답변이 장황하거나 반복될 수 있습니다.
DEFAULT_MAX_NEW_TOKENS = 40

# temperature는 다음 토큰 선택의 무작위성을 조절하는 값입니다.
# 낮을수록 안정적인 답변, 높을수록 다양한 답변이 생성됩니다.
DEFAULT_TEMPERATURE = 0.55

# top_p는 누적 확률 기준으로 후보 토큰을 제한하는 nucleus sampling 값입니다.
# 0.90이면 확률이 높은 후보부터 누적 확률 90% 안의 토큰만 사용합니다.
DEFAULT_TOP_P = 0.85

# top_k는 점수가 높은 상위 k개 후보 토큰만 사용하는 옵션입니다.
# 너무 크면 답변이 다양해지고, 너무 작으면 답변이 단조로워질 수 있습니다.
DEFAULT_TOP_K = 30

# repetition_penalty는 같은 표현이 반복되는 현상을 줄이는 값입니다.
# 1.0보다 크면 반복 토큰의 선택 확률을 낮춥니다.
DEFAULT_REPETITION_PENALTY = 1.25

# no_repeat_ngram_size는 같은 n-gram 구절 반복을 막는 옵션입니다.
# 3이면 같은 3토큰 구절이 반복 생성되는 것을 줄입니다.
DEFAULT_NO_REPEAT_NGRAM_SIZE = 4

# Streamlit 채팅창에 처음 표시할 기본 안내 문장입니다.
# 사용자가 앱을 처음 실행했을 때 사용 방법을 쉽게 이해하도록 돕습니다.
WELCOME_MESSAGE = "안녕하세요. KoGPT2 기반 한국어 챗봇입니다. 질문이나 시작 문장을 입력해 주세요."
