# 정규표현식을 사용하여 한국어 문장을 간단히 정제하기 위해 re 모듈을 불러옵니다.
import re
# 타입 힌트를 작성하기 위해 typing 모듈을 불러옵니다.
from typing import Dict, List, Tuple
# PyTorch 텐서와 신경망 기능을 사용하기 위해 torch를 불러옵니다.
import torch
# PyTorch 신경망 모듈을 사용하기 위해 nn을 불러옵니다.
from torch import nn
# PyTorch 최적화 함수를 사용하기 위해 optim을 불러옵니다.
from torch import optim


# 주문 의도를 분류할 때 사용할 라벨 목록입니다.
INTENT_LABELS = ["order", "recommend", "menu", "cart", "checkout", "smalltalk"]

# 간단한 학습 문장과 라벨을 정의합니다.
TRAIN_SAMPLES: List[Tuple[str, str]] = [
    ("아메리카노 한 잔 주문할게", "order"),
    ("카페라떼 아이스로 두 잔 주세요", "order"),
    ("카라멜 마키아토 주문", "order"),
    ("부드러운 커피 추천해줘", "recommend"),
    ("달달한 메뉴 뭐가 좋아", "recommend"),
    ("고소한 커피 추천", "recommend"),
    ("메뉴 보여줘", "menu"),
    ("커피 메뉴판 알려줘", "menu"),
    ("가격표 보여줘", "menu"),
    ("장바구니 확인", "cart"),
    ("담은 메뉴 보여줘", "cart"),
    ("주문 목록 확인", "cart"),
    ("결제할게", "checkout"),
    ("주문 완료해줘", "checkout"),
    ("계산할게", "checkout"),
    ("안녕", "smalltalk"),
    ("커피 할래", "smalltalk"),
    ("커피해", "smalltalk"),
]


# 문장을 소문자로 바꾸고 특수문자를 제거하는 함수입니다.
def normalize(text: str) -> str:
    # 영어 대소문자 차이를 줄이기 위해 소문자로 변환합니다.
    lowered = text.lower()
    # 한글, 영어, 숫자, 공백을 제외한 문자를 공백으로 바꿉니다.
    cleaned = re.sub(r"[^0-9a-zA-Z가-힣\s]", " ", lowered)
    # 여러 개의 공백을 하나의 공백으로 줄입니다.
    return re.sub(r"\s+", " ", cleaned).strip()


# 학습 문장에서 글자 단위 vocabulary를 만드는 함수입니다.
def build_vocab(samples: List[Tuple[str, str]]) -> Dict[str, int]:
    # 중복 없는 글자를 저장할 집합을 만듭니다.
    chars = set()
    # 모든 학습 문장을 순회합니다.
    for text, _ in samples:
        # 정제된 문장의 각 글자를 순회합니다.
        for ch in normalize(text):
            # 공백이 아닌 글자만 vocabulary 후보에 추가합니다.
            if ch != " ":
                chars.add(ch)
    # 정렬된 글자 목록에 인덱스를 부여하여 딕셔너리로 반환합니다.
    return {ch: idx for idx, ch in enumerate(sorted(chars))}


# 문장을 Bag-of-Characters 텐서로 변환하는 함수입니다.
def vectorize(text: str, vocab: Dict[str, int]) -> torch.Tensor:
    # vocabulary 크기만큼 0으로 채워진 벡터를 만듭니다.
    vector = torch.zeros(len(vocab), dtype=torch.float32)
    # 정제된 문장의 각 글자를 순회합니다.
    for ch in normalize(text):
        # 글자가 vocabulary에 있으면 해당 위치 값을 1 증가시킵니다.
        if ch in vocab:
            vector[vocab[ch]] += 1.0
    # 문장 길이에 따른 값 차이를 줄이기 위해 전체 합으로 나눕니다.
    if vector.sum() > 0:
        vector = vector / vector.sum()
    # 완성된 벡터를 반환합니다.
    return vector


# 간단한 의도 분류용 PyTorch 모델입니다.
class IntentClassifier(nn.Module):
    # 모델 계층을 초기화합니다.
    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int):
        # 부모 클래스 초기화를 실행합니다.
        super().__init__()
        # 첫 번째 완전연결 계층을 정의합니다.
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        # 비선형 활성화 함수 ReLU를 정의합니다.
        self.relu = nn.ReLU()
        # 출력 계층을 정의합니다.
        self.fc2 = nn.Linear(hidden_dim, output_dim)

    # 입력 텐서가 모델을 통과하는 순전파를 정의합니다.
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # 입력을 첫 번째 계층에 통과시킵니다.
        x = self.fc1(x)
        # ReLU 활성화 함수를 적용합니다.
        x = self.relu(x)
        # 출력 계층을 통과시켜 라벨별 점수를 계산합니다.
        return self.fc2(x)


# 모델, vocabulary, 라벨 매핑을 학습하여 반환하는 함수입니다.
def train_intent_model() -> tuple[IntentClassifier, Dict[str, int], Dict[str, int]]:
    # 학습 문장에서 vocabulary를 만듭니다.
    vocab = build_vocab(TRAIN_SAMPLES)
    # 라벨 문자열을 숫자 인덱스로 바꾸는 딕셔너리를 만듭니다.
    label_to_idx = {label: idx for idx, label in enumerate(INTENT_LABELS)}
    # 학습 문장을 입력 텐서 목록으로 변환합니다.
    x_data = torch.stack([vectorize(text, vocab) for text, _ in TRAIN_SAMPLES])
    # 학습 라벨을 정답 텐서로 변환합니다.
    y_data = torch.tensor([label_to_idx[label] for _, label in TRAIN_SAMPLES], dtype=torch.long)
    # 의도 분류 모델을 생성합니다.
    model = IntentClassifier(input_dim=len(vocab), hidden_dim=32, output_dim=len(INTENT_LABELS))
    # 분류 문제에 사용하는 CrossEntropyLoss를 정의합니다.
    criterion = nn.CrossEntropyLoss()
    # Adam 최적화 함수를 정의합니다.
    optimizer = optim.Adam(model.parameters(), lr=0.03)
    # 작은 데이터셋이므로 빠르게 여러 번 반복 학습합니다.
    for _ in range(250):
        # 이전 기울기를 초기화합니다.
        optimizer.zero_grad()
        # 모델 예측값을 계산합니다.
        logits = model(x_data)
        # 예측값과 정답 사이의 손실을 계산합니다.
        loss = criterion(logits, y_data)
        # 손실을 기준으로 역전파를 수행합니다.
        loss.backward()
        # 모델 가중치를 업데이트합니다.
        optimizer.step()
    # 학습된 모델을 평가 모드로 바꿉니다.
    model.eval()
    # 모델과 변환 정보를 반환합니다.
    return model, vocab, label_to_idx


# 학습된 모델 객체를 앱 시작 시 한 번만 생성합니다.
MODEL, VOCAB, LABEL_TO_IDX = train_intent_model()
# 숫자 라벨을 문자열 라벨로 되돌리기 위한 딕셔너리를 만듭니다.
IDX_TO_LABEL = {idx: label for label, idx in LABEL_TO_IDX.items()}


# 사용자 문장의 의도를 예측하는 함수입니다.
def predict_intent(text: str) -> tuple[str, float]:
    # 사용자의 문장을 모델 입력 벡터로 변환합니다.
    x = vectorize(text, VOCAB).unsqueeze(0)
    # 예측 과정에서는 기울기를 계산하지 않습니다.
    with torch.no_grad():
        # 모델 출력 점수를 계산합니다.
        logits = MODEL(x)
        # 점수를 확률로 바꿉니다.
        probs = torch.softmax(logits, dim=1).squeeze(0)
        # 가장 높은 확률의 라벨 인덱스를 구합니다.
        best_idx = int(torch.argmax(probs).item())
        # 가장 높은 확률값을 실수로 변환합니다.
        confidence = float(probs[best_idx].item())
    # 예측 라벨과 신뢰도를 반환합니다.
    return IDX_TO_LABEL[best_idx], confidence
