# 타입 힌트를 사용하기 위해 Dict, List를 불러옵니다.
from typing import Dict, List

# PyTorch 텐서와 모델을 사용하기 위해 torch를 불러옵니다.
import torch

# 신경망 계층을 만들기 위해 torch.nn을 nn 이름으로 불러옵니다.
import torch.nn as nn

# 챗봇 의도 분류에 사용할 라벨 목록입니다.
INTENT_LABELS: List[str] = ["start", "answer", "summary", "link", "help", "unknown"]

# 간단한 키워드 사전입니다.
KEYWORDS: Dict[str, List[str]] = {
    "start": ["시작", "설문", "조사", "참여", "시작할래", "응답"],
    "summary": ["요약", "결과", "확인", "정리", "내 답변"],
    "link": ["링크", "구글폼", "구글 설문", "주소", "바로가기"],
    "help": ["도움", "방법", "사용법", "메뉴", "설명"],
    "answer": ["있다", "없다", "고객상담", "교육", "쇼핑", "예약", "기타", "1", "2", "3", "4", "5"],
}

# 키워드 존재 여부를 숫자 벡터로 바꾸는 함수입니다.
def vectorize_text(text: str) -> torch.Tensor:
    # 비교를 쉽게 하기 위해 입력 문장을 소문자로 변환합니다.
    lowered_text = text.lower()

    # 각 의도별 키워드 포함 여부를 저장할 리스트입니다.
    features: List[float] = []

    # 정의된 의도 순서대로 키워드가 포함되었는지 확인합니다.
    for label in INTENT_LABELS:
        # 해당 라벨에 등록된 키워드 목록을 가져옵니다.
        words = KEYWORDS.get(label, [])

        # 하나라도 포함되면 1.0, 없으면 0.0으로 저장합니다.
        features.append(1.0 if any(word.lower() in lowered_text for word in words) else 0.0)

    # 입력 길이를 보조 특징으로 추가합니다.
    features.append(min(len(text) / 50.0, 1.0))

    # 리스트를 PyTorch float 텐서로 변환합니다.
    return torch.tensor(features, dtype=torch.float32)

# 아주 작은 의도 분류 모델입니다.
class SurveyIntentModel(nn.Module):
    # 모델 계층을 초기화합니다.
    def __init__(self) -> None:
        # 부모 클래스 초기화를 실행합니다.
        super().__init__()

        # 입력 특징 수는 의도 라벨 수 + 문장 길이 특징 1개입니다.
        input_size = len(INTENT_LABELS) + 1

        # 입력 벡터를 의도 점수로 변환하는 선형 계층입니다.
        self.classifier = nn.Linear(input_size, len(INTENT_LABELS))

        # 학습 파일 없이도 동작하도록 가중치를 규칙 기반에 가깝게 초기화합니다.
        self._init_rule_like_weights()

    # 모델 가중치를 초기화합니다.
    def _init_rule_like_weights(self) -> None:
        # 기울기 계산 없이 가중치를 직접 설정합니다.
        with torch.no_grad():
            # 모든 가중치를 0으로 초기화합니다.
            self.classifier.weight.zero_()

            # 모든 편향을 0으로 초기화합니다.
            self.classifier.bias.zero_()

            # 각 의도 특징이 자기 의도 점수에 강하게 반영되도록 설정합니다.
            for index in range(len(INTENT_LABELS)):
                # 대각선 위치의 가중치를 크게 설정합니다.
                self.classifier.weight[index, index] = 4.0

            # unknown은 길이 특징이 있어도 너무 강하지 않게 설정합니다.
            self.classifier.bias[INTENT_LABELS.index("unknown")] = 0.1

    # 순전파 함수입니다.
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # 입력 벡터를 선형 계층에 통과시켜 의도별 점수를 반환합니다.
        return self.classifier(x)

# 입력 텍스트의 의도를 예측하는 함수입니다.
def predict_intent(text: str) -> Dict[str, object]:
    # 모델 객체를 생성합니다.
    model = SurveyIntentModel()

    # 모델을 평가 모드로 전환합니다.
    model.eval()

    # 입력 문장을 숫자 벡터로 변환합니다.
    x = vectorize_text(text)

    # 배치 차원을 추가합니다.
    batch_x = x.unsqueeze(0)

    # 기울기 계산 없이 예측합니다.
    with torch.no_grad():
        # 모델 출력 점수를 계산합니다.
        logits = model(batch_x)

        # 점수를 확률로 변환합니다.
        probs = torch.softmax(logits, dim=1).squeeze(0)

        # 가장 높은 확률의 인덱스를 구합니다.
        best_index = int(torch.argmax(probs).item())

    # 예측 결과를 딕셔너리로 반환합니다.
    return {
        "intent": INTENT_LABELS[best_index],
        "confidence": round(float(probs[best_index].item()), 4),
        "scores": {label: round(float(probs[i].item()), 4) for i, label in enumerate(INTENT_LABELS)},
    }
