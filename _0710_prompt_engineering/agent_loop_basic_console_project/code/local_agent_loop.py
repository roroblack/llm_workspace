# -*- coding: utf-8 -*-
"""
local_agent_loop.py

API 키 없이 Agent Loop의 핵심 흐름을 확인하는 로컬 시뮬레이션입니다.
"""

# 정규식은 질문에서 상품 키워드를 추출하기 위해 사용합니다.
import re

# 도구 함수와 숫자 조회 함수를 가져옵니다.
from data_tools import get_stock, get_reorder_level, get_stock_number, get_reorder_number


def extract_product_keyword(question: str) -> str:
    """사용자 질문에서 실습용 상품 키워드를 단순 규칙으로 추출합니다."""
    # 스마트워치가 질문에 있으면 스마트워치를 반환합니다.
    if "스마트워치" in question:
        # 상품 검색 키워드로 사용할 문자열입니다.
        return "스마트워치"
    # 이어버드가 질문에 있으면 이어버드를 반환합니다.
    if "이어버드" in question:
        # 상품 검색 키워드로 사용할 문자열입니다.
        return "이어버드"
    # 패딩이 질문에 있으면 패딩을 반환합니다.
    if "패딩" in question:
        # 상품 검색 키워드로 사용할 문자열입니다.
        return "패딩"
    # 청바지가 질문에 있으면 청바지를 반환합니다.
    if "청바지" in question:
        # 상품 검색 키워드로 사용할 문자열입니다.
        return "청바지"
    # 아무 키워드도 찾지 못하면 기본값으로 스마트워치를 사용합니다.
    return "스마트워치"


def run_local_agent(question: str, max_steps: int = 6) -> str | None:
    """로컬 규칙으로 재고 확인 → 기준 확인 → 최종 판단 루프를 실행합니다."""
    # 상품 키워드를 질문에서 추출합니다.
    product = extract_product_keyword(question)
    # 이미 실행한 호출 서명을 저장해 반복 호출을 막습니다.
    seen_calls: set[tuple[str, str]] = set()
    # 관찰 기록을 누적할 리스트입니다.
    history: list[str] = [f"사용자 목표: {question}"]
    # 최대 max_steps만큼 반복합니다.
    for step in range(1, max_steps + 1):
        # 1단계에서는 현재 재고를 확인합니다.
        if step == 1:
            # 호출할 도구 이름을 정합니다.
            tool_name = "get_stock"
            # 호출 인자를 정합니다.
            argument = product
            # 호출 서명을 만듭니다.
            signature = (tool_name, argument)
            # 이미 같은 호출을 했다면 중복으로 판단합니다.
            if signature in seen_calls:
                # 반복 호출 경고를 출력합니다.
                print("[경고] 동일 호출 반복 감지")
                # 안전 종료합니다.
                return None
            # 호출 서명을 기록합니다.
            seen_calls.add(signature)
            # 도구를 실행합니다.
            result = get_stock(argument)
            # 실행 로그를 출력합니다.
            print(f"[STEP {step}] 호출: {tool_name} {{'product_name': '{argument}'}}")
            # 관찰 결과를 출력합니다.
            print("           관찰:", result)
            # 관찰을 history에 누적합니다.
            history.append(result)
            # 다음 반복으로 이동합니다.
            continue
        # 2단계에서는 재주문 기준을 확인합니다.
        if step == 2:
            # 호출할 도구 이름을 정합니다.
            tool_name = "get_reorder_level"
            # 호출 인자를 정합니다.
            argument = product
            # 호출 서명을 만듭니다.
            signature = (tool_name, argument)
            # 이미 같은 호출을 했다면 중복으로 판단합니다.
            if signature in seen_calls:
                # 반복 호출 경고를 출력합니다.
                print("[경고] 동일 호출 반복 감지")
                # 안전 종료합니다.
                return None
            # 호출 서명을 기록합니다.
            seen_calls.add(signature)
            # 도구를 실행합니다.
            result = get_reorder_level(argument)
            # 실행 로그를 출력합니다.
            print(f"[STEP {step}] 호출: {tool_name} {{'product_name': '{argument}'}}")
            # 관찰 결과를 출력합니다.
            print("           관찰:", result)
            # 관찰을 history에 누적합니다.
            history.append(result)
            # 다음 반복으로 이동합니다.
            continue
        # 3단계에서는 관찰 결과를 바탕으로 최종 판단합니다.
        if step == 3:
            # 현재 재고 숫자를 가져옵니다.
            stock = get_stock_number(product)
            # 재주문 기준 숫자를 가져옵니다.
            reorder = get_reorder_number(product)
            # 숫자 조회에 실패하면 안내합니다.
            if stock is None or reorder is None:
                # 최종 답변을 만듭니다.
                answer = "상품 정보를 찾지 못해 재주문 여부를 판단할 수 없습니다."
            # 재고가 기준 이하이면 재주문 필요 답변을 만듭니다.
            elif stock <= reorder:
                # 최종 답변 문자열을 만듭니다.
                answer = f"{product} 상품은 현재 재고 {stock}개, 재주문 기준 {reorder}개이므로 재주문이 필요합니다."
            # 재고가 기준보다 많으면 재주문 불필요 답변을 만듭니다.
            else:
                # 최종 답변 문자열을 만듭니다.
                answer = f"{product} 상품은 현재 재고 {stock}개, 재주문 기준 {reorder}개이므로 재주문이 필요하지 않습니다."
            # 최종 답변 단계임을 출력합니다.
            print(f"[STEP {step}] 최종 답변")
            # 최종 답변을 출력합니다.
            print(answer)
            # 최종 답변을 반환합니다.
            return answer
    # 최대 반복 횟수를 넘기면 안전장치 메시지를 출력합니다.
    print("[종료] 최대 스텝 도달 — 안전장치 작동")
    # 정상 답변이 없음을 의미합니다.
    return None


def run_local_agent_demo() -> None:
    """로컬 Agent Loop 예시 두 개를 실행합니다."""
    # 재고 부족 사례를 실행합니다.
    print("\n[예시 1] 스마트워치 재주문 판단")
    # 스마트워치 질문을 실행합니다.
    run_local_agent("스마트워치 재고를 확인하고, 재주문이 필요하면 알려줘.")
    # 재고 충분 사례를 실행합니다.
    print("\n[예시 2] 이어버드 재주문 판단")
    # 이어버드 질문을 실행합니다.
    run_local_agent("이어버드 재고 확인하고 재주문 필요한지 알려줘.")
