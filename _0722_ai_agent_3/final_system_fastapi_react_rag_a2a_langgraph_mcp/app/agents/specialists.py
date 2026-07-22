# -*- coding: utf-8 -*-
"""A2A 방식으로 역할을 나눈 전문 에이전트와 에이전트 카드를 정의합니다."""

# dataclass는 에이전트 카드 정보를 간결한 객체로 표현합니다.
from dataclasses import asdict, dataclass
# typing.Literal은 공급자 이름을 제한합니다.
from typing import Literal

# 비즈니스 서비스 함수를 가져옵니다.
from app.services.data_service import get_order_status, get_stock, request_exchange, search_faq
# 정책 RAG 검색 함수를 가져옵니다.
from app.services.rag_service import search_policy


# AgentCard는 A2A 에이전트 발견에 필요한 공개 메타데이터를 표현합니다.
@dataclass(frozen=True)
class AgentCard:
    """전문 에이전트의 이름, 설명, 기술, 엔드포인트 정보를 보관합니다."""

    # name은 에이전트의 고유 식별자입니다.
    name: str
    # description은 에이전트가 수행할 수 있는 역할 설명입니다.
    description: str
    # skills는 에이전트가 공개하는 작업 능력 목록입니다.
    skills: list[str]
    # endpoint는 A2A 메시지를 받을 HTTP 경로입니다.
    endpoint: str = "/api/v1/a2a/message"
    # version은 에이전트 카드 스키마 버전입니다.
    version: str = "1.0.0"


# AGENT_CARDS는 외부 에이전트가 발견할 수 있는 전문 에이전트 카드 목록입니다.
AGENT_CARDS = {
    "order-agent": AgentCard("order-agent", "주문 상태 전문 에이전트", ["주문번호 조회", "배송 상태 확인"]),
    "inventory-agent": AgentCard("inventory-agent", "상품 재고 전문 에이전트", ["상품명 검색", "재고 수량 확인"]),
    "faq-agent": AgentCard("faq-agent", "FAQ 검색 전문 에이전트", ["자주 묻는 질문 검색"]),
    "policy-agent": AgentCard("policy-agent", "정책 RAG 전문 에이전트", ["환불 정책", "교환 정책", "멤버십 정책"]),
    "exchange-agent": AgentCard("exchange-agent", "교환 접수 전문 에이전트", ["주문 검증", "교환 접수"]),
}


# list_agent_cards 함수는 모든 카드를 JSON 직렬화 가능한 딕셔너리로 반환합니다.
def list_agent_cards() -> list[dict[str, object]]:
    """A2A 발견용 에이전트 카드 목록을 반환합니다."""
    # dataclass 객체를 일반 딕셔너리로 변환합니다.
    return [asdict(card) for card in AGENT_CARDS.values()]


# _extract_order_id 함수는 교육용 메시지에서 O로 시작하는 주문번호를 찾습니다.
def _extract_order_id(message: str) -> str:
    """자연어 메시지에서 O000000 형식의 주문번호를 추출합니다."""
    # 정규표현식 모듈을 함수 내부에서 가져옵니다.
    import re
    # 대소문자와 무관하게 주문번호 패턴을 검색합니다.
    match = re.search(r"\bO\d{6}\b", message, flags=re.IGNORECASE)
    # 주문번호가 있으면 대문자로 변환해 반환합니다.
    if match:
        # 일관된 비교를 위해 대문자로 변환합니다.
        return match.group(0).upper()
    # 주문번호가 없으면 빈 문자열을 반환합니다.
    return ""


# delegate_to_agent 함수는 대상 전문 에이전트에 작업을 위임합니다.
def delegate_to_agent(
    target_agent: str,
    message: str,
    provider: Literal["openai", "gemini"],
) -> str:
    """A2A 게이트웨이처럼 대상 에이전트의 능력에 맞춰 요청을 전달합니다."""
    # 주문 전문 에이전트 요청인지 확인합니다.
    if target_agent == "order-agent":
        # 메시지에서 주문번호를 추출합니다.
        order_id = _extract_order_id(message)
        # 주문번호가 없으면 필요한 형식을 안내합니다.
        if not order_id:
            # 전문 에이전트가 명확화 요청을 반환합니다.
            return "주문번호를 O000000 형식으로 입력해 주세요."
        # 실제 주문 서비스 결과를 반환합니다.
        return get_order_status(order_id)
    # 재고 전문 에이전트 요청인지 확인합니다.
    if target_agent == "inventory-agent":
        # 교육용 구현에서는 전체 메시지를 상품 검색어로 사용합니다.
        return get_stock(message)
    # FAQ 전문 에이전트 요청인지 확인합니다.
    if target_agent == "faq-agent":
        # 전체 메시지를 FAQ 검색 키워드로 전달합니다.
        return search_faq(message)
    # 정책 RAG 전문 에이전트 요청인지 확인합니다.
    if target_agent == "policy-agent":
        # 공급자별 임베딩을 사용하여 정책 문서를 검색합니다.
        return search_policy(message, provider)
    # 교환 접수 전문 에이전트 요청인지 확인합니다.
    if target_agent == "exchange-agent":
        # 메시지에서 주문번호를 추출합니다.
        order_id = _extract_order_id(message)
        # 주문번호가 없으면 교환 접수를 중단하고 입력을 요청합니다.
        if not order_id:
            # 주문 검증 없는 쓰기 작업을 방지합니다.
            return "교환할 주문번호를 O000000 형식으로 입력해 주세요."
        # 메시지 전체를 교환 사유로 기록하는 교육용 처리입니다.
        return request_exchange(order_id, message)
    # 등록되지 않은 에이전트 이름이면 오류를 반환합니다.
    return f"등록되지 않은 A2A 에이전트입니다: {target_agent}"
