"""저장된(또는 사전학습) 한국어 감성분석 모델을 불러와 문장 긍정/부정을 예측하는 파일입니다.

영어용 `src/predict.py` 의 SentimentPredictor 와 같은 인터페이스(predict -> dict)를 제공하여
Streamlit 앱에서 영어용과 동일한 방식으로 사용할 수 있습니다.
"""

from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from src_choi_yeonwoo.config import DEFAULT_MODEL_NAME, ID_TO_LABEL, MAX_LEN, MODEL_DIR
from src_choi_yeonwoo.utils import get_device


def _resolve_positive_index(model) -> int:
    """모델 설정(id2label)을 보고 '긍정' 클래스의 인덱스를 찾습니다.

    모델마다 라벨 순서가 다를 수 있으므로(0=긍정인 모델도 있음) 라벨 문자열을 보고 판단하고,
    판단이 불가능하면 NSMC 관례(1=긍정)를 따릅니다.
    """
    # 모델 설정에 id2label 정보가 있으면 그것을 사용합니다.
    id2label = getattr(model.config, "id2label", None) or {}

    # 라벨 문자열에 긍정을 뜻하는 표현이 있으면 해당 인덱스를 긍정으로 봅니다.
    for idx, label in id2label.items():
        text = str(label).lower()
        if ("pos" in text) or ("긍정" in text) or text == "1":
            return int(idx)

    # 판단이 불가능하면 NSMC 관례에 따라 1번을 긍정으로 사용합니다.
    return 1


class KoreanSentimentPredictor:
    """Streamlit과 다른 Python 코드에서 재사용할 수 있는 한국어 감성분석 예측 클래스입니다."""

    def __init__(
        self,
        model_dir: str | Path = MODEL_DIR,
        fallback_model_name: str = DEFAULT_MODEL_NAME,
        max_len: int = MAX_LEN,
    ):
        # 모델 저장 경로를 Path 객체로 변환합니다.
        self.model_dir = Path(model_dir)

        # 로컬 모델이 없을 때 대신 사용할 Hugging Face 모델명을 저장합니다.
        self.fallback_model_name = fallback_model_name

        # 모델 입력 최대 토큰 길이를 저장합니다.
        self.max_len = max_len

        # GPU 또는 CPU 실행 장치를 선택합니다.
        self.device = get_device()

        # 직접 파인튜닝한 로컬 모델 폴더가 있으면 그것을, 없으면 사전학습 NSMC 모델을 사용합니다.
        self.load_path = str(self.model_dir) if self.model_dir.exists() else self.fallback_model_name

        # 학습 때 사용한 것과 같은 Tokenizer를 불러옵니다.
        self.tokenizer = AutoTokenizer.from_pretrained(self.load_path)

        # 이진 분류용 모델을 불러옵니다.
        self.model = AutoModelForSequenceClassification.from_pretrained(self.load_path)

        # 모델을 선택된 장치로 이동합니다.
        self.model.to(self.device)

        # 예측만 수행하므로 평가 모드로 전환합니다.
        self.model.eval()

        # 이 모델에서 '긍정' 클래스가 몇 번 인덱스인지 미리 계산해 둡니다.
        self.positive_index = _resolve_positive_index(self.model)

    def predict(self, text: str) -> dict[str, float | str]:
        """입력 문장 하나에 대해 부정/긍정 예측 결과와 확률을 반환합니다."""
        # 빈 문장을 예측하지 않도록 앞뒤 공백을 제거합니다.
        text = text.strip()

        # 사용자가 문장을 입력하지 않은 경우 명확한 오류를 발생시킵니다.
        if not text:
            raise ValueError("예측할 문장을 입력하세요.")

        # 입력 문장을 모델 입력 텐서로 변환합니다.
        encoded = self.tokenizer(
            text,
            add_special_tokens=True,
            max_length=self.max_len,
            return_attention_mask=True,
            return_tensors="pt",
            padding="max_length",
            truncation=True,
        )

        # 입력 텐서를 모델이 위치한 장치로 이동합니다.
        encoded = {key: value.to(self.device) for key, value in encoded.items()}

        # 예측 과정에서는 기울기 계산이 필요 없으므로 torch.no_grad()로 메모리 사용량을 줄입니다.
        with torch.no_grad():
            # 모델에 입력을 넣어 각 클래스에 대한 로짓을 계산합니다.
            outputs = self.model(**encoded)

            # 로짓을 확률처럼 해석할 수 있도록 softmax를 적용합니다.
            probabilities = torch.softmax(outputs.logits, dim=-1).squeeze(0)

        # 긍정/부정 인덱스를 모델 설정에 맞춰 가져옵니다.
        positive_index = self.positive_index
        negative_index = 1 - positive_index

        # 긍정 확률이 0.5 이상이면 긍정, 아니면 부정으로 판단합니다.
        positive_probability = float(probabilities[positive_index].item())
        negative_probability = float(probabilities[negative_index].item())
        predicted_label = 1 if positive_probability >= negative_probability else 0

        # 예측 결과를 화면 출력에 편한 딕셔너리 형태로 반환합니다.
        return {
            "label": ID_TO_LABEL[predicted_label],
            "negative_probability": negative_probability,
            "positive_probability": positive_probability,
            "model_path": self.load_path,
        }


if __name__ == "__main__":
    # 간단한 동작 확인용 예시입니다.
    predictor = KoreanSentimentPredictor()
    for sample in ["이 영화 정말 재미있어요. 강력 추천합니다.", "시간 낭비였어요. 정말 별로네요."]:
        result = predictor.predict(sample)
        print(sample, "->", result["label"], f"(긍정 {result['positive_probability']:.4f})")
