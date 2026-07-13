"""BBC 기사 분류 실습용 샘플 데이터 생성 모듈."""

from __future__ import annotations

from typing import List, Tuple


# BBC 기사 분류를 목표로 하며 sport, business, politics, tech, entertainment 계열의 라벨을 다룬다.
# 실제 BBC 원본 데이터 파일이 없는 환경에서도 실행되도록 각 분야별 영문 샘플 기사를 내장했다.
SAMPLE_DATA: List[Tuple[str, str]] = [
    ("The football team won the final after scoring two late goals in the stadium", "sport"),
    ("The tennis champion reached the semi final with a powerful serve and fast return", "sport"),
    ("A young striker signed a new contract before the league match this weekend", "sport"),
    ("The coach praised the players after the club moved to the top of the table", "sport"),
    ("Olympic athletes trained hard for the swimming race and cycling event", "sport"),
    ("The central bank increased interest rates to slow inflation and protect the economy", "business"),
    ("Shares rose sharply after the company reported strong quarterly profit", "business"),
    ("The airline announced job cuts as fuel prices increased across the market", "business"),
    ("Investors watched the stock market closely after the trade deal was announced", "business"),
    ("Retail sales improved as consumers spent more during the holiday season", "business"),
    ("The prime minister answered questions about the new education policy in parliament", "politics"),
    ("Voters will choose a new president after weeks of national election debate", "politics"),
    ("The government proposed a law to reform public health services", "politics"),
    ("Opposition leaders criticised the budget plan during a televised speech", "politics"),
    ("The mayor promised to improve transport and housing after winning the vote", "politics"),
    ("The smartphone maker released a new device with faster artificial intelligence features", "tech"),
    ("Researchers developed software that detects security attacks on cloud servers", "tech"),
    ("A startup built a robot that can learn from voice commands and camera images", "tech"),
    ("The company updated its mobile app with improved privacy controls", "tech"),
    ("Scientists used machine learning to analyse large amounts of online text", "tech"),
    ("The actor won an award for a drama film at the international festival", "entertainment"),
    ("The singer released a new album after a successful concert tour", "entertainment"),
    ("A popular television show returned with new characters and a surprising story", "entertainment"),
    ("The movie director announced the release date for a comedy sequel", "entertainment"),
    ("Fans watched the music performance live during the weekend broadcast", "entertainment"),
]


def load_sample_data() -> Tuple[List[str], List[str]]:
    """내장 샘플 데이터를 기사 문장 목록과 라벨 목록으로 분리해서 반환한다."""

    texts = [text for text, _ in SAMPLE_DATA]    # 각 튜플의 첫 번째 값인 기사 문장만 모은다.
    labels = [label for _, label in SAMPLE_DATA] # 각 튜플의 두 번째 값인 카테고리 라벨만 모은다.
    return texts, labels                         # 모델 학습에 사용할 입력 데이터와 정답 데이터를 반환한다.
