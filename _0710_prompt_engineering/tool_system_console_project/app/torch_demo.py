# -*- coding: utf-8 -*-
"""PyTorch로 상품/재고 데이터를 간단히 수치 분석하는 실습 모듈입니다."""

from __future__ import annotations

# torch는 텐서 계산을 위해 사용합니다.
import torch

# data_tools는 CSV를 읽어 둔 DataFrame을 제공합니다.
from data_tools import inventory, products


def run_torch_summary() -> None:
    """상품 가격과 재고를 텐서로 변환하여 평균, 최댓값, 부족 재고를 계산합니다."""
    # 상품 가격 컬럼을 float32 텐서로 변환합니다.
    price_tensor = torch.tensor(products["price"].tolist(), dtype=torch.float32)
    # 재고 수량 컬럼을 float32 텐서로 변환합니다.
    stock_tensor = torch.tensor(inventory["stock"].tolist(), dtype=torch.float32)
    # 평균 가격을 계산합니다.
    avg_price = torch.mean(price_tensor)
    # 최고 가격을 계산합니다.
    max_price = torch.max(price_tensor)
    # 평균 재고를 계산합니다.
    avg_stock = torch.mean(stock_tensor)
    # 재고가 10개 이하인 상품을 부족 재고로 판단합니다.
    low_stock_mask = stock_tensor <= 10
    # True인 위치의 인덱스를 가져옵니다.
    low_stock_indices = torch.nonzero(low_stock_mask, as_tuple=False).flatten().tolist()
    # 계산 결과를 출력합니다.
    print("\n[PyTorch 상품/재고 텐서 분석]")
    print(f"평균 가격: {avg_price.item():,.0f}원")
    print(f"최고 가격: {max_price.item():,.0f}원")
    print(f"평균 재고: {avg_stock.item():.1f}개")
    print("재고 10개 이하 상품:")
    # 부족 재고 상품명을 출력합니다.
    for index in low_stock_indices:
        product_name = inventory.iloc[index]["product_name"]
        stock = int(inventory.iloc[index]["stock"])
        print(f"- {product_name}: {stock}개")
