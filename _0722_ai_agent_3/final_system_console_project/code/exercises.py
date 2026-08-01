# -*- coding: utf-8 -*-
"""실습문제 해답을 독립 실행할 수 있게 구현한 모듈입니다."""

# 교환 접수번호의 난수 부분을 만들기 위해 random 모듈을 가져옵니다.
import random
# 영문 대문자와 숫자 문자 집합을 사용하기 위해 string 모듈을 가져옵니다.
import string
# 주문번호가 실제 데이터에 존재하는지 확인하기 위해 원시 주문 조회 함수를 가져옵니다.
from data_tools import get_order_status_raw


def request_exchange_raw(order_id: str, reason: str) -> str:
    """실습 1 해답: 실제 주문 검증 후 교환 접수번호를 생성합니다."""
    # 사용자가 입력한 주문번호를 공백 제거와 대문자 변환으로 정규화합니다.
    normalized = order_id.strip().upper()
    # 실제 orders.csv를 조회해 해당 주문이 존재하는지 확인합니다.
    order_result = get_order_status_raw(normalized)
    # 조회 결과에 찾을 수 없다는 문구가 있으면 쓰기 작업을 진행하지 않습니다.
    if "찾을 수 없습니다" in order_result:
        return f"교환을 접수할 수 없습니다. {order_result}"
    # 교환 사유의 앞뒤 공백을 제거합니다.
    normalized_reason = reason.strip()
    # 사유가 비어 있으면 접수에 필요한 정보를 다시 요청합니다.
    if not normalized_reason:
        return "교환 사유를 입력해 주세요."
    # 대문자와 숫자 중 여섯 글자를 무작위로 선택합니다.
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    # EX 접두사와 난수 문자열을 결합해 교육용 교환 접수번호를 만듭니다.
    ticket = f"EX-{suffix}"
    # 실제 서비스에서는 DB INSERT가 필요한 지점임을 포함해 결과 문장을 반환합니다.
    return (
        f"교환 접수가 완료되었습니다. 접수번호: {ticket}\n"
        f"주문번호: {normalized}\n"
        f"교환 사유: {normalized_reason}\n"
        "영업일 기준 1~2일 내 담당자가 연락드립니다."
    )


def run_exchange_exercise() -> None:
    """실습 1 해답을 콘솔 입력으로 실행합니다."""
    # 사용자에게 교환할 주문번호를 입력받습니다.
    order_id = input("교환할 주문번호를 입력하세요 [기본 O000050]: ").strip() or "O000050"
    # 사용자에게 구체적인 교환 사유를 입력받습니다.
    reason = input("교환 사유를 입력하세요 [기본 상품 불량]: ").strip() or "상품 불량"
    # 검증과 접수번호 생성을 수행한 결과를 출력합니다.
    print(request_exchange_raw(order_id, reason))


def run_memory_isolation_exercise() -> None:
    """실습 2 해답: 서로 다른 thread_id가 독립 세션임을 실제 에이전트로 검증합니다."""
    # API를 사용하는 최종 answer 함수를 지연 import해 다른 메뉴 실행에 영향을 주지 않게 합니다.
    from final_agent import answer
    # 첫 번째 고객 세션의 식별자를 지정합니다.
    thread_a = "exercise-user-a"
    # 두 번째 고객 세션의 식별자를 지정합니다.
    thread_b = "exercise-user-b"
    # A 세션에 환불 정책 질문을 저장하고 답변을 출력합니다.
    print("\n[A-1]", answer("환불 절차 알려줘", thread_id=thread_a))
    # B 세션에는 재고 질문을 저장하고 답변을 출력합니다.
    print("\n[B-1]", answer("스마트워치 재고를 알려줘", thread_id=thread_b))
    # A 세션에서 '아까 그 정책'을 질문해 A의 환불 맥락이 이어지는지 확인합니다.
    print("\n[A-2]", answer("아까 그 정책을 다시 알려줘", thread_id=thread_a))
    # B 세션에서 같은 표현을 사용해 A의 맥락이 섞이지 않는지 확인합니다.
    print("\n[B-2]", answer("아까 그 정책을 다시 알려줘", thread_id=thread_b))
    # 관찰해야 할 핵심 기준을 화면에 출력합니다.
    print("\n[관찰] A와 B의 이전 대화가 서로 섞이지 않아야 합니다.")
