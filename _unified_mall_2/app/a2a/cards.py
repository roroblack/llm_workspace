"""A2A 전문 에이전트 카드 — 발견(discovery)용 공개 메타데이터.

프레임워크 무의존(dataclass·stdlib만). 외부/다른 에이전트가 이 카드를 읽어 어떤 전문
에이전트에게 무엇을 위임할 수 있는지 파악한다(A2A의 핵심: 능력의 공개적 발견).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

# 위임 메시지를 받는 공통 엔드포인트(모든 카드 동일).
_A2A_ENDPOINT = "/api/a2a/message"


@dataclass(frozen=True)
class AgentCard:
    """전문 에이전트의 이름·설명·능력·수신 엔드포인트·버전."""

    name: str
    description: str
    skills: list[str]
    endpoint: str = _A2A_ENDPOINT
    version: str = "1.0.0"


# 등록된 전문 에이전트. 각 능력은 기존 서비스에 매핑된다(gateway 참조).
AGENT_CARDS: dict[str, AgentCard] = {
    "order-agent": AgentCard(
        "order-agent", "주문 상태 전문 에이전트", ["주문번호 조회", "배송 상태 확인"]
    ),
    "catalog-agent": AgentCard(
        "catalog-agent", "상품·재고 전문 에이전트", ["상품 검색", "재고 조회", "가격 조회"]
    ),
    "knowledge-agent": AgentCard(
        "knowledge-agent", "정책·FAQ 지식 검색 전문 에이전트(RAG)", ["정책 검색", "FAQ 검색"]
    ),
    "recommend-agent": AgentCard(
        "recommend-agent", "상품 추천 전문 에이전트", ["임베딩 유사도 추천"]
    ),
}


def list_agent_cards() -> list[dict[str, object]]:
    """A2A 발견용 — 모든 카드를 JSON 직렬화 가능한 딕셔너리 목록으로 반환."""
    return [asdict(card) for card in AGENT_CARDS.values()]
