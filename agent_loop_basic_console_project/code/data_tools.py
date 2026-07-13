# -*- coding: utf-8 -*-
"""
data_tools.py

Agent Loop 실습에서 사용할 재고 조회 도구 함수를 정의합니다.
"""

# pandas는 CSV 데이터를 표 형태로 읽고 검색하기 위해 사용합니다.
import pandas as pd

# common.py에서 DATA 경로를 가져옵니다.
from common import DATA

# inventory.csv 파일을 읽어 재고 데이터프레임으로 저장합니다.
inventory_df = pd.read_csv(DATA / "inventory.csv")


def get_stock(product_name: str) -> str:
    """상품명(일부만 입력해도 됨)을 받아 현재 재고 수량을 반환한다."""
    # 상품명 일부가 포함된 행을 찾습니다.
    row = inventory_df[inventory_df["product_name"].str.contains(product_name, na=False)]
    # 일치하는 상품이 없으면 안내 문자열을 반환합니다.
    if row.empty:
        # 모델이나 사용자에게 보여 줄 안전한 실패 메시지입니다.
        return f"'{product_name}' 재고 정보 없음"
    # 첫 번째 검색 결과 행을 선택합니다.
    r = row.iloc[0]
    # 상품명과 현재 재고 수량을 문자열로 반환합니다.
    return f"{r['product_name']} 현재 재고 {int(r['stock'])}개"


def get_reorder_level(product_name: str) -> str:
    """상품명을 받아 재주문 기준 수량(reorder_level)을 반환한다. 재고가 이 값 이하이면 재주문이 필요하다."""
    # 상품명 일부가 포함된 행을 찾습니다.
    row = inventory_df[inventory_df["product_name"].str.contains(product_name, na=False)]
    # 일치하는 상품이 없으면 안내 문자열을 반환합니다.
    if row.empty:
        # 모델이나 사용자에게 보여 줄 안전한 실패 메시지입니다.
        return f"'{product_name}' 재주문 기준 정보 없음"
    # 첫 번째 검색 결과 행을 선택합니다.
    r = row.iloc[0]
    # 상품명과 재주문 기준 수량을 문자열로 반환합니다.
    return f"{r['product_name']} 재주문 기준 {int(r['reorder_level'])}개"


def get_stock_number(product_name: str) -> int | None:
    """Torch 실습용으로 현재 재고 수량을 정수로 반환합니다."""
    # 상품명 일부가 포함된 행을 찾습니다.
    row = inventory_df[inventory_df["product_name"].str.contains(product_name, na=False)]
    # 일치하는 행이 없으면 None을 반환합니다.
    if row.empty:
        # 검색 실패를 의미합니다.
        return None
    # 재고 수량을 정수로 변환해 반환합니다.
    return int(row.iloc[0]["stock"])


def get_reorder_number(product_name: str) -> int | None:
    """Torch 실습용으로 재주문 기준 수량을 정수로 반환합니다."""
    # 상품명 일부가 포함된 행을 찾습니다.
    row = inventory_df[inventory_df["product_name"].str.contains(product_name, na=False)]
    # 일치하는 행이 없으면 None을 반환합니다.
    if row.empty:
        # 검색 실패를 의미합니다.
        return None
    # 재주문 기준 수량을 정수로 변환해 반환합니다.
    return int(row.iloc[0]["reorder_level"])

# 모델이 반환한 함수 이름으로 실제 파이썬 함수를 찾기 위한 딕셔너리입니다.
TOOLS = {
    # get_stock이라는 이름은 현재 재고 조회 함수에 연결합니다.
    "get_stock": get_stock,
    # get_reorder_level이라는 이름은 재주문 기준 조회 함수에 연결합니다.
    "get_reorder_level": get_reorder_level,
}
