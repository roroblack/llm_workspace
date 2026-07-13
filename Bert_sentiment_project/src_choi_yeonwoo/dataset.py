"""PyTorch Dataset 클래스를 정의하는 파일입니다.

영어용 `src/dataset.py` 와 동일한 구조이지만, BERT 전용 토크나이저 대신
어떤 한국어 모델 토크나이저(KoELECTRA/KoBERT 등)와도 동작하도록 일반 토크나이저를 받습니다.
"""

import torch


class KoreanSentimentDataset(torch.utils.data.Dataset):
    """문장과 정답 라벨을 모델 입력 텐서로 변환하는 Dataset 클래스입니다."""

    def __init__(self, reviews, labels, tokenizer, max_len: int = 64):
        # 리뷰 문장 리스트를 저장합니다.
        self.reviews = list(reviews)

        # 정답 라벨 리스트를 저장합니다. 0은 부정, 1은 긍정입니다.
        self.labels = list(labels)

        # 문장을 토큰 ID로 변환할 Hugging Face Tokenizer를 저장합니다.
        self.tokenizer = tokenizer

        # 각 문장을 최대 몇 개 토큰까지 사용할지 저장합니다.
        self.max_len = max_len

    def __len__(self) -> int:
        # Dataset 전체 샘플 수를 반환합니다.
        return len(self.reviews)

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        # 현재 인덱스에 해당하는 문장을 문자열로 가져옵니다.
        review = str(self.reviews[index])

        # 현재 인덱스에 해당하는 정답 라벨을 정수로 가져옵니다.
        label = int(self.labels[index])

        # Tokenizer를 사용하여 문장을 모델 입력 형식으로 변환합니다.
        encoded = self.tokenizer(
            review,
            add_special_tokens=True,
            max_length=self.max_len,
            return_attention_mask=True,
            return_tensors="pt",
            padding="max_length",
            truncation=True,
        )

        # Trainer가 이해하는 딕셔너리 형태로 입력 텐서와 정답 라벨을 반환합니다.
        item = {
            "input_ids": encoded["input_ids"].squeeze(0),
            "attention_mask": encoded["attention_mask"].squeeze(0),
            "labels": torch.tensor(label, dtype=torch.long),
        }

        # 일부 모델(BERT 계열)은 token_type_ids 도 사용하므로 있으면 함께 전달합니다.
        if "token_type_ids" in encoded:
            item["token_type_ids"] = encoded["token_type_ids"].squeeze(0)

        return item
