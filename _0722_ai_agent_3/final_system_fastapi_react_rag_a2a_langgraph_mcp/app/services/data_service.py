# -*- coding: utf-8 -*-
"""data.zip에서 추출한 CSV 파일을 조회하고 교환 접수를 처리하는 서비스입니다."""

# random은 교환 접수번호에 사용할 임의 문자를 선택합니다.
import random
# string은 영문 대문자와 숫자 문자 집합을 제공합니다.
import string
# threading.Lock은 동시에 여러 요청이 들어올 때 CSV 로딩을 안전하게 보호합니다.
from threading import Lock

# pandas는 CSV 데이터를 DataFrame으로 읽고 검색합니다.
import pandas as pd

# DATA_DIR은 data.zip의 실제 데이터가 위치하는 경로입니다.
from app.core.settings import DATA_DIR

# _data_lock은 최초 데이터 로딩 시 경쟁 상태를 방지합니다.
_data_lock = Lock()
# _tables는 한 번 읽은 CSV를 메모리에 저장하는 모듈 캐시입니다.
_tables: dict[str, pd.DataFrame] = {}


# _load_table 함수는 지정한 CSV를 한 번만 읽고 재사용합니다.
def _load_table(file_name: str) -> pd.DataFrame:
    """CSV 파일을 지연 로딩하여 캐시된 DataFrame을 반환합니다."""
    # 이미 로드된 데이터라면 파일을 다시 읽지 않고 즉시 반환합니다.
    if file_name in _tables:
        # 캐시된 DataFrame을 반환합니다.
        return _tables[file_name]
    # 여러 요청이 동시에 최초 로딩을 시도하지 않도록 잠금을 획득합니다.
    with _data_lock:
        # 잠금 대기 중 다른 요청이 로딩했을 수 있으므로 다시 확인합니다.
        if file_name not in _tables:
            # 프로젝트 data 폴더에서 요청한 CSV 파일을 읽습니다.
            _tables[file_name] = pd.read_csv(DATA_DIR / file_name)
    # 최종적으로 캐시된 DataFrame을 반환합니다.
    return _tables[file_name]


# get_order_status는 주문번호로 실제 주문 데이터를 검색합니다.
def get_order_status(order_id: str) -> str:
    """orders.csv에서 주문 상태, 상품, 수량, 금액을 조회합니다."""
    # 사용자가 입력한 주문번호의 공백을 제거하고 대문자로 통일합니다.
    normalized_id = order_id.strip().upper()
    # 주문 CSV를 캐시에서 가져옵니다.
    orders = _load_table("orders.csv")
    # order_id 열이 정규화된 주문번호와 같은 행만 추출합니다.
    hit = orders[orders["order_id"].astype(str).str.upper() == normalized_id]
    # 검색 결과가 없으면 환각 없이 명확한 실패 메시지를 반환합니다.
    if hit.empty:
        # 찾지 못한 주문번호를 함께 표시합니다.
        return f"주문번호 {normalized_id}를 찾을 수 없습니다."
    # 첫 번째 검색 결과를 Series로 가져옵니다.
    row = hit.iloc[0]
    # 필요한 열이 데이터에 있는지 확인하며 안전하게 값을 가져옵니다.
    product_name = row.get("product_name", "상품명 미상")
    # 수량을 읽고 정수 문자열로 변환합니다.
    quantity = int(row.get("quantity", 0))
    # 금액을 읽고 천 단위 쉼표 형식으로 변환합니다.
    amount = int(float(row.get("amount", 0)))
    # 주문일을 문자열로 읽습니다.
    order_date = row.get("order_date", "주문일 미상")
    # 주문 상태를 문자열로 읽습니다.
    status = row.get("status", "상태 미상")
    # 사용자에게 읽기 쉬운 한 문장으로 조합하여 반환합니다.
    return (
        f"주문 {normalized_id}: {product_name} {quantity}개, "
        f"{amount:,}원, 주문일 {order_date}, 상태={status}"
    )


# get_stock은 상품명 일부를 이용해 재고를 검색합니다.
def get_stock(product_name: str) -> str:
    """inventory.csv에서 상품명과 재고 수량을 조회합니다."""
    # 검색 키워드의 앞뒤 공백을 제거합니다.
    keyword = product_name.strip()
    # 재고 CSV를 캐시에서 가져옵니다.
    inventory = _load_table("inventory.csv")
    # 데이터셋마다 상품명 열 이름이 다를 수 있으므로 후보를 순서대로 찾습니다.
    name_column = next(
        (column for column in ["product_name", "name", "product"] if column in inventory.columns),
        None,
    )
    # 상품명 열을 찾지 못한 경우 데이터 구조 오류를 반환합니다.
    if name_column is None:
        # 개발자가 CSV 열을 확인할 수 있는 메시지를 반환합니다.
        return "inventory.csv에서 상품명 열을 찾을 수 없습니다."
    # 대소문자와 정규식 영향을 제거한 부분 문자열 검색을 수행합니다.
    hit = inventory[inventory[name_column].astype(str).str.contains(keyword, case=False, regex=False, na=False)]
    # 검색 결과가 없으면 임의 재고 수량을 생성하지 않습니다.
    if hit.empty:
        # 오타 또는 미등록 상품일 수 있음을 명확히 알립니다.
        return f"'{keyword}' 상품의 재고 정보를 찾을 수 없습니다."
    # 가장 먼저 일치한 상품 행을 선택합니다.
    row = hit.iloc[0]
    # 재고 수량 열 이름 후보를 순서대로 찾습니다.
    stock_column = next(
        (column for column in ["stock", "stock_quantity", "quantity", "inventory"] if column in inventory.columns),
        None,
    )
    # 재고 열이 없으면 열 구조 오류를 반환합니다.
    if stock_column is None:
        # 개발자가 CSV 구조를 수정할 수 있도록 안내합니다.
        return "inventory.csv에서 재고 수량 열을 찾을 수 없습니다."
    # 실제 상품명을 읽습니다.
    matched_name = row[name_column]
    # 재고 수량을 정수로 변환합니다.
    stock_value = int(float(row[stock_column]))
    # 조회 결과를 사용자 친화적인 문장으로 반환합니다.
    return f"상품 '{matched_name}'의 현재 재고는 {stock_value:,}개입니다."


# search_faq는 FAQ 질문과 답변에서 키워드를 검색합니다.
def search_faq(keyword: str) -> str:
    """faq.csv에서 키워드와 관련된 FAQ 답변을 검색합니다."""
    # 검색어의 불필요한 공백을 제거합니다.
    normalized_keyword = keyword.strip()
    # FAQ CSV를 캐시에서 가져옵니다.
    faq = _load_table("faq.csv")
    # 질문 열 이름 후보를 찾습니다.
    question_column = next(
        (column for column in ["question", "faq_question", "title"] if column in faq.columns),
        None,
    )
    # 답변 열 이름 후보를 찾습니다.
    answer_column = next(
        (column for column in ["answer", "faq_answer", "content"] if column in faq.columns),
        None,
    )
    # 필수 열이 없으면 데이터 구조 오류를 반환합니다.
    if question_column is None or answer_column is None:
        # FAQ 스키마를 확인하라는 메시지를 반환합니다.
        return "faq.csv에서 질문 또는 답변 열을 찾을 수 없습니다."
    # 질문과 답변을 합친 문자열에서 키워드를 검색합니다.
    combined = faq[question_column].astype(str) + " " + faq[answer_column].astype(str)
    # 대소문자와 정규식 영향을 제거하여 관련 행을 필터링합니다.
    hit = faq[combined.str.contains(normalized_keyword, case=False, regex=False, na=False)]
    # 관련 FAQ가 없으면 솔직한 실패 메시지를 반환합니다.
    if hit.empty:
        # 검색어를 포함해 사용자가 다른 표현을 시도할 수 있게 합니다.
        return f"'{normalized_keyword}'와 관련된 FAQ를 찾지 못했습니다."
    # 가장 먼저 일치한 FAQ 행을 선택합니다.
    row = hit.iloc[0]
    # 질문과 답변을 함께 반환해 근거를 확인할 수 있게 합니다.
    return f"FAQ 질문: {row[question_column]}\nFAQ 답변: {row[answer_column]}"


# request_exchange는 쓰기 행동 도구의 교육용 예시입니다.
def request_exchange(order_id: str, reason: str) -> str:
    """실제 주문 존재 여부를 확인한 뒤 교환 접수번호를 생성합니다."""
    # 주문번호를 표준 형식으로 정규화합니다.
    normalized_id = order_id.strip().upper()
    # 주문이 실제 존재하는지 먼저 조회합니다.
    order_result = get_order_status(normalized_id)
    # 찾을 수 없다는 문구가 포함되면 잘못된 주문으로 판단합니다.
    if "찾을 수 없습니다" in order_result:
        # 존재하지 않는 주문에는 접수번호를 만들지 않습니다.
        return order_result + " 따라서 교환을 접수하지 않았습니다."
    # 교환 사유의 공백을 제거합니다.
    normalized_reason = reason.strip()
    # 사유가 비어 있으면 추가 입력을 요청합니다.
    if not normalized_reason:
        # 쓰기 작업 전에 필수 정보를 확인합니다.
        return "교환 사유를 입력해 주세요."
    # 영문 대문자와 숫자 중에서 6개 문자를 무작위로 선택합니다.
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    # EX 접두사를 붙여 교환 접수번호를 완성합니다.
    ticket = f"EX-{suffix}"
    # 교육용 접수 결과를 상세히 반환합니다.
    return (
        f"교환 접수가 완료되었습니다. 접수번호: {ticket}\n"
        f"주문번호: {normalized_id}\n교환 사유: {normalized_reason}\n"
        "영업일 기준 1~2일 내 담당자가 연락드립니다."
    )


# list_data_files는 웹 화면에서 사용 데이터 목록을 보여 줍니다.
def list_data_files() -> list[dict[str, object]]:
    """data 폴더의 CSV, JSON, PDF 파일 정보를 반환합니다."""
    # 결과 목록을 빈 리스트로 초기화합니다.
    result: list[dict[str, object]] = []
    # data 폴더 아래의 모든 파일을 재귀적으로 순회합니다.
    for path in sorted(DATA_DIR.rglob("*")):
        # 디렉터리는 제외하고 실제 파일만 처리합니다.
        if path.is_file():
            # 프로젝트 기준 상대 경로와 파일 크기를 저장합니다.
            result.append({"name": str(path.relative_to(DATA_DIR)), "size": path.stat().st_size})
    # 완성된 파일 정보 목록을 반환합니다.
    return result
