"""BBC 기사 분류 RNN 프로젝트 설정 파일."""

from dataclasses import dataclass

'''
@dataclass 장식자 (decorator : 데코레이터)
데이터를 저장하기 위한 클래스에 주로 사용함

일반적인 class 작성 코드:
class 클래스명:
    def __init__(self) -> None:
        self.필드명 = 초기값
        ......
    def __repr__(self) -> str:
        # 저장된 필드값들을 하나의 문자열(문장)로 만들어서 출력하는 메소드
        .....
    def __eq__(self, other: object) -> bool:
        # 다른 Config 객체 안의 필드값들과 이 객체 안의 필드값들이 모두 일치하는지 확인하는 메소드
        if isinstance(other, Config):
            return self.필드명 == oher.필드명 and .........

=> 클래스 이름위에 @dataclass 표시하면 
init(), repr(), eq() 를 자동 생성해 주는 데코레이터임
'''

@dataclass
class Config:
    """학습과 예측에 공통으로 사용하는 하이퍼파라미터를 한 곳에서 관리하는 클래스."""

    max_vocab: int = 5000          # 토큰화에 사용할 최대 단어 수이다.
    max_len: int = 80              # 모든 기사 문장의 길이를 동일하게 맞추기 위한 최대 토큰 길이이다.
    embed_dim: int = 64            # 각 단어 정수를 몇 차원의 임베딩 벡터로 바꿀지 정한다.
    hidden_dim: int = 64           # LSTM 내부 은닉 상태의 차원 수이다.
    batch_size: int = 8            # 한 번의 학습 단계에서 모델에 넣을 샘플 개수이다.
    epochs: int = 8                # 전체 학습 데이터를 몇 번 반복해서 학습할지 정한다.
    learning_rate: float = 0.001   # Adam 최적화 알고리즘의 학습률이다.
    test_size: float = 0.25        # 전체 데이터 중 평가 데이터로 사용할 비율이다.
    random_state: int = 42         # 실험 결과를 재현하기 위한 난수 고정값이다.
    model_path: str = "../models/bbc_lstm_model.pt"  # 학습된 모델을 저장할 경로이다.
