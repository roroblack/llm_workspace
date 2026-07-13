# -*- coding: utf-8 -*-
"""PyTorch 텐서를 사용해 분류 정확도 계산 원리를 확인하는 실습 모듈입니다."""

# pandas는 CSV 데이터를 읽고 표 형태로 다루기 위해 사용합니다.
import pandas as pd

# torch는 텐서 연산으로 정확도 계산 과정을 보여 주기 위해 사용합니다.
import torch

# common.py의 DATA 경로를 사용하여 data/cs_inquiries.csv를 안정적으로 찾습니다.
from common import DATA


# run_torch_accuracy_demo 함수는 API 호출 없이 텐서 기반 정확도 계산을 보여 줍니다.
def run_torch_accuracy_demo() -> None:
    # 고객 문의 CSV 파일을 pandas DataFrame으로 읽습니다.
    df = pd.read_csv(DATA / "cs_inquiries.csv", encoding="utf-8-sig")
    # 실습을 빠르게 보여 주기 위해 앞의 10개 행만 사용합니다.
    sample_df = df.head(10).copy()
    # 예측값 예시를 정답과 거의 같게 만들되 일부러 마지막 2개는 틀리게 만들어 오분류를 만듭니다.
    sample_df["pred"] = sample_df["category_hint"].tolist()
    # 9번째 예측값을 결제로 바꿔 일부러 오답을 만듭니다.
    sample_df.loc[sample_df.index[-2], "pred"] = "환불"
    # 10번째 예측값을 배송으로 바꿔 일부러 오답을 만듭니다.
    sample_df.loc[sample_df.index[-1], "pred"] = "불만"
    # pred와 category_hint가 같은지 비교한 결과를 bool 리스트로 만듭니다.
    correct_list = (sample_df["pred"] == sample_df["category_hint"]).tolist()
    # bool 리스트를 float32 텐서로 바꾸면 True는 1.0, False는 0.0으로 변환됩니다.
    correct_tensor = torch.tensor(correct_list, dtype=torch.float32)
    # 평균을 구하면 맞은 비율, 즉 정확도가 됩니다.
    accuracy = correct_tensor.mean().item()
    # 실습 데이터 표를 콘솔에 출력합니다.
    print(sample_df[["content", "category_hint", "pred"]].to_string(index=False))
    # 텐서 값을 출력하여 True/False가 1/0으로 계산되는 과정을 확인합니다.
    print("\n정답 여부 텐서:", correct_tensor)
    # 최종 정확도를 백분율로 출력합니다.
    print(f"PyTorch 텐서 정확도: {accuracy:.1%} ({int(correct_tensor.sum().item())}/{len(correct_tensor)})")
