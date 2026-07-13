"""저장된 BERT 감성분석 모델을 불러와 문장 긍정/부정을 예측하는 파일입니다."""

from pathlib import Path

import torch
from transformers import BertForSequenceClassification, BertTokenizerFast

from src.config import DEFAULT_MODEL_NAME, ID_TO_LABEL, MAX_LEN, MODEL_DIR
from src.utils import get_device


class SentimentPredictor:
    """Streamlit과 다른 Python 코드에서 재사용할 수 있는 감성분석 예측 클래스입니다."""

    def __init__(self, model_dir: str | Path = MODEL_DIR, fallback_model_name: str = DEFAULT_MODEL_NAME, max_len: int = MAX_LEN):
        # 모델 저장 경로를 Path 객체로 변환합니다.
        self.model_dir = Path(model_dir)

        # 로컬 모델이 없을 때 대신 사용할 Hugging Face 모델명을 저장합니다.
        self.fallback_model_name = fallback_model_name

        # BERT 입력 최대 토큰 길이를 저장합니다.
        self.max_len = max_len

        # GPU 또는 CPU 실행 장치를 선택합니다.
        self.device = get_device()

        # 로컬 모델 폴더가 있으면 그 폴더에서 모델을 불러오고, 없으면 기본 사전 학습 모델을 불러옵니다.
        self.load_path = str(self.model_dir) if self.model_dir.exists() else self.fallback_model_name

        # 학습 때 사용한 것과 같은 Tokenizer를 불러옵니다.
        self.tokenizer = BertTokenizerFast.from_pretrained(self.load_path)

        # 이진 분류용 BERT 모델을 불러옵니다.
        self.model = BertForSequenceClassification.from_pretrained(self.load_path, num_labels=2)

        # 모델을 선택된 장치로 이동합니다.
        self.model.to(self.device)

        # 예측만 수행하므로 dropout 등을 비활성화하는 평가 모드로 전환합니다.
        self.model.eval()

    def predict(self, text: str) -> dict[str, float | str]:
        """입력 문장 하나에 대해 부정/긍정 예측 결과와 확률을 반환합니다."""
        # 빈 문장을 예측하지 않도록 앞뒤 공백을 제거합니다.
        text = text.strip()

        # 사용자가 문장을 입력하지 않은 경우 명확한 오류를 발생시킵니다.
        if not text:
            raise ValueError("예측할 문장을 입력하세요.")

        # 입력 문장을 BERT 입력 텐서로 변환합니다.
        encoded = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=self.max_len,
            return_token_type_ids=False,
            return_attention_mask=True,
            return_tensors="pt",
            padding="max_length",
            truncation=True,
        )

        # 입력 텐서를 모델이 위치한 장치로 이동합니다.
        input_ids = encoded["input_ids"].to(self.device)

        # attention_mask도 같은 장치로 이동합니다.
        attention_mask = encoded["attention_mask"].to(self.device)

        # 예측 과정에서는 기울기 계산이 필요 없으므로 torch.no_grad()로 메모리 사용량을 줄입니다.
        with torch.no_grad():
            # 모델에 입력을 넣어 각 클래스에 대한 로짓을 계산합니다.
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)

            # 로짓을 확률처럼 해석할 수 있도록 softmax를 적용합니다.
            probabilities = torch.softmax(outputs.logits, dim=-1).squeeze(0)

            # 가장 확률이 높은 클래스 번호를 가져옵니다.
            predicted_id = int(torch.argmax(probabilities).item())

        # 예측 결과를 화면 출력에 편한 딕셔너리 형태로 반환합니다.
        return {
            "label": ID_TO_LABEL[predicted_id],
            "negative_probability": float(probabilities[0].item()),
            "positive_probability": float(probabilities[1].item()),
            "model_path": self.load_path,
        }
