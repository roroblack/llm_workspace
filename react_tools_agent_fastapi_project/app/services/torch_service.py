# -*- coding: utf-8 -*-
"""
Torch 기반 분석 서비스입니다.

이 프로젝트에서 torch는 두 가지 역할을 합니다.
  1) 재고와 재주문 기준을 텐서로 변환해 재주문 필요 상품을 계산합니다.
  2) Vector DB 검색에서 코사인 유사도 계산을 수행합니다.
"""

# torch는 텐서 계산을 위해 사용합니다.
import torch

# 도구 서비스에서 재고 데이터를 dict 형태로 가져옵니다.
from app.services.tools_service import local_stock_summary


def analyze_inventory_with_torch() -> dict:
    """재고 데이터에서 재주문 필요 상품을 Torch 텐서 연산으로 계산합니다."""
    # CSV에서 읽은 재고 레코드를 가져옵니다.
    rows = local_stock_summary()

    # 상품명 리스트를 만듭니다.
    names = [row["product_name"] for row in rows]

    # 현재 재고 수량을 float32 텐서로 변환합니다.
    stock_tensor = torch.tensor([row["stock"] for row in rows], dtype=torch.float32)

    # 재주문 기준 수량을 float32 텐서로 변환합니다.
    reorder_tensor = torch.tensor([row["reorder_level"] for row in rows], dtype=torch.float32)

    # 현재 재고가 재주문 기준 이하인지 Boolean 텐서로 계산합니다.
    need_reorder_mask = stock_tensor <= reorder_tensor

    # 전체 상품 수를 계산합니다.
    total_count = len(rows)

    # 재주문 필요 상품 수를 계산합니다.
    need_count = int(need_reorder_mask.sum().item())

    # 재주문 필요 상품 목록을 만듭니다.
    need_items = [names[i] for i, flag in enumerate(need_reorder_mask.tolist()) if flag]

    # 평균 재고 수량을 계산합니다.
    avg_stock = float(stock_tensor.mean().item())

    # 분석 결과를 dict로 반환합니다.
    return {
        "total_products": total_count,
        "need_reorder_count": need_count,
        "need_reorder_items": need_items,
        "average_stock": round(avg_stock, 2),
    }
