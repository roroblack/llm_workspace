# -*- coding: utf-8 -*-
"""제6강 Tool System 실습용 도구 함수와 데이터 로드 모듈입니다."""

from __future__ import annotations

# pandas는 CSV 파일을 DataFrame으로 읽고 조건 검색하는 데 사용합니다.
import pandas as pd

# DATA는 common.py에서 제공하는 공통 데이터 폴더 경로입니다.
from common import DATA


# products.csv는 상품 ID, 상품명, 카테고리, 가격 정보를 담습니다.
products = pd.read_csv(DATA / "products.csv", encoding="utf-8")
# inventory.csv는 상품명, 재고 수량, 창고 정보를 담습니다.
inventory = pd.read_csv(DATA / "inventory.csv", encoding="utf-8")
# orders.csv는 주문번호, 상품명, 수량, 배송 상태 정보를 담습니다.
orders = pd.read_csv(DATA / "orders.csv", encoding="utf-8")


def get_price(product_name: str) -> str:
    """상품명(일부만 입력해도 됨)을 받아 판매가(원)를 반환한다. 가격/얼마 질문에 사용."""
    # 상품명 컬럼에서 입력 문자열이 포함된 행을 찾습니다.
    row = products[products["product_name"].str.contains(product_name, na=False)]
    # 검색 결과가 없으면 모델이 읽을 수 있는 안내 문자열을 반환합니다.
    if row.empty:
        return f"'{product_name}' 가격 정보를 찾지 못했습니다."
    # 첫 번째 검색 결과를 선택합니다.
    r = row.iloc[0]
    # 가격을 쉼표가 포함된 원화 문자열로 반환합니다.
    return f"{r['product_name']} 판매가 {int(r['price']):,}원"


def get_stock(product_name: str) -> str:
    """상품명(일부만 입력해도 됨)을 받아 현재 재고 수량과 창고를 반환한다. 재고/품절 질문에 사용."""
    # 재고 데이터에서 상품명이 입력 문자열을 포함하는 행을 찾습니다.
    row = inventory[inventory["product_name"].str.contains(product_name, na=False)]
    # 검색 결과가 없으면 예외 대신 안내 문자열을 반환합니다.
    if row.empty:
        return f"'{product_name}' 재고 정보를 찾지 못했습니다."
    # 첫 번째 검색 결과를 선택합니다.
    r = row.iloc[0]
    # 상품명, 재고 수량, 창고명을 사람이 읽는 문자열로 반환합니다.
    return f"{r['product_name']} 재고 {int(r['stock'])}개 ({r['warehouse']})"


def get_order_status(order_id: str) -> str:
    """주문번호(예: O000106)를 받아 배송 상태를 반환한다. 주문/배송 추적에 사용."""
    # 주문번호가 정확히 일치하는 행을 찾습니다.
    row = orders[orders["order_id"] == order_id]
    # 주문번호가 없으면 안내 문자열을 반환합니다.
    if row.empty:
        return f"주문번호 {order_id}를 찾지 못했습니다."
    # 첫 번째 검색 결과를 선택합니다.
    r = row.iloc[0]
    # 주문 상태를 사람이 읽는 문자열로 반환합니다.
    return f"주문 {order_id}: {r['product_name']} {int(r['quantity'])}개, 상태={r['status']}"


def search_product(keyword: str) -> str:
    """카테고리나 키워드로 상품을 검색해 이름 목록을 반환한다. '어떤 상품 있어?' 류에 사용."""
    # 상품명 또는 카테고리에 키워드가 포함된 상품을 찾습니다.
    hit = products[
        products["product_name"].str.contains(keyword, na=False)
        | products["category"].str.contains(keyword, na=False)
    ]
    # 검색 결과가 없으면 안내 문자열을 반환합니다.
    if hit.empty:
        return f"'{keyword}' 관련 상품이 없습니다."
    # 최대 5개 상품명을 목록으로 묶어 반환합니다.
    return "검색 결과: " + ", ".join(hit["product_name"].head(5).tolist())


def get_product_info_clear(product_id: str) -> str:
    """[정확검색] 상품ID(예: P0001)로 정확히 1건의 상세정보(이름/카테고리/가격)를 반환한다. 상품ID를 이미 알 때만 사용. 상품명·키워드로는 사용하지 말 것."""
    # 상품 ID가 정확히 일치하는 행을 찾습니다.
    row = products[products["product_id"] == product_id]
    # 상품 ID가 없으면 안내 문자열을 반환합니다.
    if row.empty:
        return f"상품ID {product_id} 상세정보를 찾지 못했습니다."
    # 첫 번째 검색 결과를 선택합니다.
    r = row.iloc[0]
    # 상세 정보를 문자열로 반환합니다.
    return f"{r['product_id']} {r['product_name']} / 카테고리={r['category']} / 가격={int(r['price']):,}원"


def search_product_clear(keyword: str) -> str:
    """[키워드검색] 상품명 일부(예: '이어버드', '청바지')로 여러 후보를 찾아 이름 목록을 반환한다. 상품ID를 모르고 이름·키워드만 알 때 사용."""
    # 상품명에 키워드가 포함된 상품 후보를 찾습니다.
    hit = products[products["product_name"].str.contains(keyword, na=False)]
    # 후보가 없으면 안내 문자열을 반환합니다.
    if hit.empty:
        return f"'{keyword}' 키워드 상품 후보가 없습니다."
    # 후보 목록을 문자열로 반환합니다.
    return "상품 후보: " + ", ".join(hit["product_name"].tolist())


# Gemini SDK에 전달할 기본 도구 목록입니다.
GEMINI_TOOLS = [get_price, get_stock, get_order_status, search_product]

# 이름으로 실제 파이썬 함수를 찾기 위한 매핑입니다.
TOOL_MAP = {
    "get_price": get_price,
    "get_stock": get_stock,
    "get_order_status": get_order_status,
    "search_product": search_product,
    "get_product_info_clear": get_product_info_clear,
    "search_product_clear": search_product_clear,
}
