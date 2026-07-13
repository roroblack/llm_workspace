# -*- coding: utf-8 -*-
"""Function Calling에 연결할 재고 조회/환율 조회 도구 함수 모듈입니다."""

# pandas는 CSV 데이터를 DataFrame으로 읽고 검색하기 위해 사용합니다.
import pandas as pd

# torch는 재고 수량을 텐서로 변환해 기본 통계 계산을 확인하기 위해 사용합니다.
import torch

# common.py에서 실습 데이터 폴더 경로를 가져옵니다.
from common import DATA

# 재고 DB 다운 상황을 실습하기 위한 전역 스위치입니다.
DB_DOWN = False


def load_inventory() -> pd.DataFrame:
    """data/inventory.csv 파일을 읽어 재고 DataFrame으로 반환합니다."""
    # DATA 경로 아래 inventory.csv 파일을 UTF-8 기본 인코딩으로 읽습니다.
    return pd.read_csv(DATA / "inventory.csv")


def load_exchange_rates() -> pd.DataFrame:
    """data/exchange_rates.csv 파일을 읽어 환율 DataFrame으로 반환합니다."""
    # DATA 경로 아래 exchange_rates.csv 파일을 읽습니다.
    return pd.read_csv(DATA / "exchange_rates.csv")


def get_stock(product_name: str) -> str:
    """상품명 일부 또는 전체 이름을 받아 현재 재고 수량과 창고 위치를 반환한다."""
    # 함수 내부에서 예외를 처리하여 에이전트 전체가 중단되지 않게 합니다.
    try:
        # DB_DOWN이 True이면 실제 장애처럼 예외를 강제로 발생시킵니다.
        if DB_DOWN:
            raise ConnectionError("재고 DB 연결 실패(timeout)")
        # 재고 CSV를 DataFrame으로 읽습니다.
        inv = load_inventory()
        # product_name 컬럼에서 사용자가 입력한 상품명이 포함된 행을 찾습니다.
        row = inv[inv["product_name"].str.contains(product_name, na=False)]
        # 검색 결과가 없으면 예외 대신 안내 문자열을 반환합니다.
        if row.empty:
            return f"'{product_name}' 상품을 찾을 수 없습니다. 상품명을 다시 확인해 주세요."
        # 첫 번째 검색 결과 행을 선택합니다.
        r = row.iloc[0]
        # 재고 수량, 창고, 가격을 사람이 읽기 좋은 문자열로 반환합니다.
        return f"{r['product_name']} 재고 {int(r['stock'])}개 / 창고: {r['warehouse']} / 가격: {int(r['price_krw']):,}원"
    # 모든 예외를 잡아 사용자 안내 메시지로 변환합니다.
    except Exception as e:
        return f"일시적인 시스템 오류로 재고를 조회하지 못했습니다. 잠시 후 다시 시도해 주세요. 사유: {e}"


def get_exchange_rate(currency: str) -> str:
    """통화 코드(USD, EUR, JPY, CNY)를 받아 1단위당 원화(KRW) 환율을 반환한다."""
    # 예외 처리를 통해 잘못된 입력이나 파일 오류에도 프로그램이 멈추지 않게 합니다.
    try:
        # 환율 CSV를 DataFrame으로 읽습니다.
        rates = load_exchange_rates()
        # 통화 코드를 대문자로 통일하여 비교합니다.
        row = rates[rates["currency"].str.upper() == currency.upper()]
        # 없는 통화 코드이면 안내 문자열을 반환합니다.
        if row.empty:
            return f"{currency} 환율 정보가 없습니다. 지원 통화: USD, EUR, JPY, CNY"
        # 환율 값을 float으로 변환합니다.
        krw = float(row.iloc[0]["krw_per_unit"])
        # 환율 정보를 문자열로 반환합니다.
        return f"1 {currency.upper()} = {krw:,.2f} KRW"
    # 예외가 발생하면 모델이 처리할 수 있는 문자열로 반환합니다.
    except Exception as e:
        return f"일시적인 시스템 오류로 환율을 조회하지 못했습니다. 사유: {e}"


def torch_inventory_summary() -> None:
    """PyTorch 텐서로 재고 수량의 합계, 평균, 품절 개수를 계산합니다."""
    # 재고 데이터를 읽습니다.
    inv = load_inventory()
    # stock 컬럼을 float32 텐서로 변환합니다.
    stock_tensor = torch.tensor(inv["stock"].tolist(), dtype=torch.float32)
    # 총 재고 수량을 계산합니다.
    total_stock = torch.sum(stock_tensor).item()
    # 평균 재고 수량을 계산합니다.
    avg_stock = torch.mean(stock_tensor).item()
    # 0개인 상품 수를 계산합니다.
    zero_count = torch.sum(stock_tensor == 0).item()
    # 결과를 출력합니다.
    print("[Torch 재고 통계]")
    print(f"재고 텐서: {stock_tensor}")
    print(f"총 재고 수량: {int(total_stock)}개")
    print(f"평균 재고 수량: {avg_stock:.2f}개")
    print(f"품절 상품 수: {int(zero_count)}개")


def test_tools_without_llm() -> None:
    """LLM 연결 전에 도구 함수가 정상 작동하는지 직접 호출합니다."""
    # 재고 도구를 직접 호출합니다.
    print(get_stock("이어버드"))
    # 환율 도구를 직접 호출합니다.
    print(get_exchange_rate("USD"))
    # 없는 상품 처리를 확인합니다.
    print(get_stock("존재하지않는상품XYZ"))
    # 없는 통화 처리를 확인합니다.
    print(get_exchange_rate("ZZZ"))
