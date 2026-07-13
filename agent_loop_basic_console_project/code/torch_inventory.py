# -*- coding: utf-8 -*-
"""
torch_inventory.py

Torch 텐서를 사용해 재고와 재주문 기준을 비교하는 기본 실습입니다.
"""

# torch는 숫자 배열을 텐서로 변환하고 벡터 연산을 수행하기 위해 사용합니다.
import torch

# pandas는 CSV 재고 데이터를 읽기 위해 사용합니다.
import pandas as pd

# common.py에서 DATA 경로를 가져옵니다.
from common import DATA


def run_torch_inventory_demo() -> None:
    """inventory.csv를 읽어 Torch 텐서로 재주문 필요 여부를 계산합니다."""
    # inventory.csv 파일을 데이터프레임으로 읽습니다.
    df = pd.read_csv(DATA / "inventory.csv")
    # stock 컬럼을 float32 텐서로 변환합니다.
    stock = torch.tensor(df["stock"].tolist(), dtype=torch.float32)
    # reorder_level 컬럼을 float32 텐서로 변환합니다.
    reorder = torch.tensor(df["reorder_level"].tolist(), dtype=torch.float32)
    # 현재 재고가 재주문 기준 이하이면 True가 되는 불리언 텐서를 만듭니다.
    need_reorder = stock <= reorder
    # 재고 부족 정도를 계산합니다. 기준보다 부족한 양만 양수로 남깁니다.
    shortage = torch.clamp(reorder - stock, min=0)
    # 전체 상품 수를 출력합니다.
    print("전체 상품 수:", len(df))
    # 평균 재고 수량을 출력합니다.
    print("평균 재고:", float(stock.mean()))
    # 재주문 필요 상품 수를 출력합니다.
    print("재주문 필요 상품 수:", int(need_reorder.sum().item()))
    # 상품별 결과를 반복 출력합니다.
    for i, row in df.iterrows():
        # 현재 행의 재주문 필요 여부를 bool로 변환합니다.
        flag = bool(need_reorder[i].item())
        # 현재 행의 부족 수량을 정수로 변환합니다.
        gap = int(shortage[i].item())
        # 상품명, 재고, 기준, 재주문 여부를 출력합니다.
        print(f"- {row['product_name']} | 재고={row['stock']} | 기준={row['reorder_level']} | 재주문필요={flag} | 부족={gap}")
