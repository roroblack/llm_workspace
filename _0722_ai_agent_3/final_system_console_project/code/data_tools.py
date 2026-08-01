# -*- coding: utf-8 -*-
"""orders.csv, inventory.csv, faq.csv를 조회하는 핵심 도구 모듈입니다."""

# 표 형태 CSV 파일을 읽고 검색하기 위해 pandas를 가져옵니다.
import pandas as pd
# 공통 모듈의 data 폴더 경로를 가져옵니다.
from common import DATA

# 주문 CSV를 모듈 로드 시 한 번만 읽어 반복 호출 비용을 줄입니다.
ORDERS = pd.read_csv(DATA / "orders.csv")
# 재고 CSV를 모듈 로드 시 한 번만 읽어 반복 호출 비용을 줄입니다.
INVENTORY = pd.read_csv(DATA / "inventory.csv")
# FAQ CSV를 모듈 로드 시 한 번만 읽어 반복 호출 비용을 줄입니다.
FAQ = pd.read_csv(DATA / "faq.csv")


def get_order_status_raw(order_id: str) -> str:
    """주문번호로 주문 상태, 상품, 수량, 금액과 주문일을 조회합니다."""
    # 사용자가 입력한 주문번호의 공백을 제거하고 대문자로 통일합니다.
    normalized = order_id.strip().upper()
    # order_id 열에서 정규화된 주문번호와 같은 행만 선택합니다.
    matched = ORDERS[ORDERS["order_id"].astype(str).str.upper() == normalized]
    # 일치하는 행이 없으면 거짓 정보를 만들지 않고 찾을 수 없다고 반환합니다.
    if matched.empty:
        return f"주문번호 {normalized or '(빈 값)'}를 찾을 수 없습니다."
    # 첫 번째 일치 행을 Series 객체로 꺼냅니다.
    row = matched.iloc[0]
    # CSV 열이 일부 달라도 안전하게 값을 얻도록 Series.get을 사용합니다.
    product_name = row.get("product_name", "상품명 정보 없음")
    # 수량 값을 가져오고 누락되면 물음표를 사용합니다.
    quantity = row.get("quantity", "?")
    # 금액 값을 가져오고 숫자이면 천 단위 쉼표 형식으로 변환합니다.
    amount_value = row.get("amount", 0)
    # 숫자 변환이 가능한 경우 정수 금액 문자열을 생성합니다.
    try:
        amount_text = f"{int(float(amount_value)):,}원"
    # 값이 숫자가 아니면 원본 값을 문자열로 사용합니다.
    except (TypeError, ValueError):
        amount_text = str(amount_value)
    # 주문일과 상태 값을 안전하게 읽습니다.
    order_date = row.get("order_date", "주문일 정보 없음")
    # 상태 열이 없을 때 사용할 기본 문구를 지정합니다.
    status = row.get("status", "상태 정보 없음")
    # 실제 CSV에서 읽은 정보를 사람이 읽기 쉬운 한 문장으로 반환합니다.
    return f"주문 {normalized}: {product_name} {quantity}개, {amount_text}, 주문일 {order_date}, 상태={status}"


def get_stock_raw(product_name: str) -> str:
    """상품명 일부 또는 전체를 이용해 재고를 조회합니다."""
    # 검색어의 앞뒤 공백을 제거해 검색 품질을 높입니다.
    keyword = product_name.strip()
    # 빈 검색어는 모든 행과 일치할 수 있으므로 즉시 안내 메시지를 반환합니다.
    if not keyword:
        return "조회할 상품명을 입력해 주세요."
    # 실제 상품명 열 이름을 자동 탐색해 데이터 형식 차이에 대응합니다.
    name_column = "product_name" if "product_name" in INVENTORY.columns else INVENTORY.columns[0]
    # 대소문자를 구분하지 않는 부분 문자열 검색으로 상품 행을 찾습니다.
    matched = INVENTORY[INVENTORY[name_column].astype(str).str.contains(keyword, case=False, na=False)]
    # 일치 상품이 없으면 수량을 지어내지 않고 정보가 없다고 반환합니다.
    if matched.empty:
        return f"'{keyword}' 상품의 재고 정보를 찾을 수 없습니다."
    # 검색 결과가 여러 개일 수 있으므로 최대 5개까지만 문장으로 구성합니다.
    lines = []
    # 최대 5개 행을 순회해 상품별 재고 문장을 만듭니다.
    for _, row in matched.head(5).iterrows():
        # 재고 수량 열 이름 후보 중 실제 존재하는 첫 열을 찾습니다.
        stock_column = next((column for column in ["stock", "quantity", "stock_quantity", "inventory"] if column in INVENTORY.columns), None)
        # 재고 열이 있으면 해당 값을 사용하고 없으면 정보 없음으로 표시합니다.
        stock_value = row.get(stock_column, "정보 없음") if stock_column else "정보 없음"
        # 상품 한 건의 결과를 목록에 추가합니다.
        lines.append(f"{row.get(name_column)}: 재고 {stock_value}")
    # 여러 결과를 줄바꿈으로 연결해 반환합니다.
    return "\n".join(lines)


def search_faq_raw(keyword: str) -> str:
    """FAQ 질문과 답변에서 키워드를 검색합니다."""
    # 검색어의 공백을 제거합니다.
    normalized = keyword.strip()
    # 빈 검색어가 입력되면 구체적인 키워드를 요청합니다.
    if not normalized:
        return "검색할 FAQ 키워드를 입력해 주세요."
    # FAQ의 질문 열 이름을 자동 선택합니다.
    question_column = "question" if "question" in FAQ.columns else FAQ.columns[0]
    # FAQ의 답변 열 이름을 자동 선택합니다.
    answer_column = "answer" if "answer" in FAQ.columns else FAQ.columns[min(1, len(FAQ.columns) - 1)]
    # 질문과 답변을 합친 문자열에서 키워드를 부분 검색합니다.
    combined = FAQ[question_column].astype(str) + " " + FAQ[answer_column].astype(str)
    # 대소문자를 구분하지 않고 키워드를 포함하는 행만 선택합니다.
    matched = FAQ[combined.str.contains(normalized, case=False, na=False)]
    # 검색 결과가 없으면 관련 FAQ를 찾지 못했다고 정직하게 알립니다.
    if matched.empty:
        return "관련 FAQ를 찾지 못했습니다."
    # 최대 3개의 FAQ를 보기 쉬운 형식으로 구성합니다.
    results = [f"Q. {row[question_column]}\nA. {row[answer_column]}" for _, row in matched.head(3).iterrows()]
    # 각 FAQ 사이에 구분선 역할의 줄바꿈을 넣어 반환합니다.
    return "\n\n".join(results)


def build_langchain_tools():
    """원시 조회 함수를 LangChain @tool 객체 3개로 변환해 반환합니다."""
    # LangChain 도구 데코레이터를 함수 내부에서 가져와 비LLM 메뉴의 의존성을 줄입니다.
    from langchain_core.tools import tool

    # 주문 관련 질문에 사용할 주문 조회 도구를 정의합니다.
    @tool
    def get_order_status(order_id: str) -> str:
        """주문번호(예: O000050)로 실제 주문 상태, 상품, 수량, 금액과 주문일을 조회한다."""
        # 검증된 원시 주문 조회 함수를 호출하고 결과를 반환합니다.
        return get_order_status_raw(order_id)

    # 상품 재고 질문에 사용할 재고 조회 도구를 정의합니다.
    @tool
    def get_stock(product_name: str) -> str:
        """상품명 전체 또는 일부를 이용해 실제 inventory.csv 재고 정보를 조회한다."""
        # 검증된 원시 재고 조회 함수를 호출하고 결과를 반환합니다.
        return get_stock_raw(product_name)

    # 배송, 결제, 반품 등 자주 묻는 질문에 사용할 FAQ 도구를 정의합니다.
    @tool
    def search_faq(keyword: str) -> str:
        """배송, 결제, 반품 등 자주 묻는 질문을 faq.csv에서 키워드로 검색한다."""
        # 검증된 원시 FAQ 검색 함수를 호출하고 결과를 반환합니다.
        return search_faq_raw(keyword)

    # 에이전트에 전달할 세 도구를 리스트로 묶어 반환합니다.
    return [get_order_status, get_stock, search_faq]
