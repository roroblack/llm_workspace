# -*- coding: utf-8 -*-
"""
ReAct 에이전트가 사용할 도구 함수 모듈입니다.

도구 설계 원칙:
  1) 한 도구는 한 가지 일만 수행합니다.
  2) 함수 이름은 기능을 바로 알 수 있게 작성합니다.
  3) 인자 이름은 모델이 채우기 쉽게 명확하게 작성합니다.
  4) 독스트링에는 '무엇을 하는가'와 '언제 쓰는가'를 적습니다.
  5) 반환값은 항상 문자열로 통일합니다.
"""

# pandas는 CSV 데이터를 읽고 필터링하기 위해 사용합니다.
import pandas as pd

# langchain_core.tools의 tool 데코레이터는 함수를 LangChain 도구로 등록합니다.
from langchain_core.tools import tool

# common 모듈에서 data 폴더 경로를 가져옵니다.
from common import DATA

# Vector DB 검색 함수를 가져옵니다.
from app.services.vector_db import search_vector_db


# products.csv 파일을 DataFrame으로 읽습니다.
products = pd.read_csv(DATA / "products.csv")

# inventory.csv 파일을 DataFrame으로 읽습니다.
inventory = pd.read_csv(DATA / "inventory.csv")

# orders.csv 파일을 DataFrame으로 읽습니다.
orders = pd.read_csv(DATA / "orders.csv")


@tool
def get_price(product_name: str) -> str:
    """상품명 일부를 받아 판매가(원)를 반환한다. 가격/얼마/판매가 질문에 사용한다."""
    # 상품명에 입력 문자열이 포함된 행을 찾습니다.
    row = products[products["product_name"].str.contains(product_name, na=False)]

    # 검색 결과가 없으면 안내 문자열을 반환합니다.
    if row.empty:
        return f"'{product_name}' 가격 정보를 찾지 못했습니다."

    # 첫 번째 검색 결과 행을 가져옵니다.
    r = row.iloc[0]

    # 상품명과 가격을 사람이 읽기 쉬운 문자열로 반환합니다.
    return f"{r['product_name']} 판매가는 {int(r['price']):,}원입니다."


@tool
def get_stock(product_name: str) -> str:
    """상품명 일부를 받아 현재 재고 수량과 창고를 반환한다. 재고/품절/남은 수량 질문에 사용한다."""
    # 상품명에 입력 문자열이 포함된 재고 행을 찾습니다.
    row = inventory[inventory["product_name"].str.contains(product_name, na=False)]

    # 검색 결과가 없으면 안내 문자열을 반환합니다.
    if row.empty:
        return f"'{product_name}' 재고 정보를 찾지 못했습니다."

    # 첫 번째 검색 결과 행을 가져옵니다.
    r = row.iloc[0]

    # 재고 수량과 창고 정보를 문자열로 반환합니다.
    return f"{r['product_name']} 현재 재고는 {int(r['stock'])}개이며, 보관 창고는 {r['warehouse']}입니다."


@tool
def get_reorder_level(product_name: str) -> str:
    """상품명 일부를 받아 재주문 기준 수량을 반환한다. 재주문 필요 여부 판단에 사용한다."""
    # 상품명에 입력 문자열이 포함된 행을 찾습니다.
    row = inventory[inventory["product_name"].str.contains(product_name, na=False)]

    # 검색 결과가 없으면 안내 문자열을 반환합니다.
    if row.empty:
        return f"'{product_name}' 재주문 기준 정보를 찾지 못했습니다."

    # 첫 번째 검색 결과 행을 가져옵니다.
    r = row.iloc[0]

    # 재주문 기준 수량을 문자열로 반환합니다.
    return f"{r['product_name']} 재주문 기준은 {int(r['reorder_level'])}개입니다."


@tool
def get_order_status(order_id: str) -> str:
    """주문번호(예: O000106)를 받아 주문 상품, 수량, 배송 상태를 반환한다. 주문/배송 추적 질문에 사용한다."""
    # 주문번호가 정확히 일치하는 행을 찾습니다.
    row = orders[orders["order_id"] == order_id]

    # 주문번호가 없으면 안내 문자열을 반환합니다.
    if row.empty:
        return f"주문번호 {order_id}를 찾지 못했습니다."

    # 첫 번째 주문 행을 가져옵니다.
    r = row.iloc[0]

    # 주문 상태를 문자열로 반환합니다.
    return f"주문 {order_id}: {r['product_name']} {int(r['quantity'])}개, 현재 상태는 {r['status']}입니다."


@tool
def search_knowledge_base(query: str) -> str:
    """ReAct, 도구 설계, Agent Loop, 무한루프 방지 같은 강의 지식을 Vector DB에서 검색한다."""
    # Vector DB에서 query와 유사한 문서 3개를 검색합니다.
    results = search_vector_db(query=query, top_k=3)

    # 검색 결과가 없으면 안내 문자열을 반환합니다.
    if not results:
        return "관련 지식 문서를 찾지 못했습니다."

    # 결과를 사람이 읽기 쉬운 여러 줄 문자열로 변환합니다.
    lines = [f"[{item['source']} | score={item['score']}] {item['text'][:300]}" for item in results]

    # 줄바꿈으로 결합하여 반환합니다.
    return "\n\n".join(lines)


def local_stock_summary() -> dict:
    """Torch 실습용 재고 통계를 계산하기 위해 재고 DataFrame을 dict 형태로 반환합니다."""
    # DataFrame의 주요 컬럼을 dict 리스트로 변환합니다.
    return inventory[["product_name", "stock", "reorder_level", "warehouse"]].to_dict(orient="records")


# LangChain에 등록할 도구 목록입니다.
TOOLS = [get_price, get_stock, get_reorder_level, get_order_status, search_knowledge_base]

# 이름으로 도구 객체를 찾기 위한 딕셔너리입니다.
TOOL_MAP = {tool.name: tool for tool in TOOLS}
