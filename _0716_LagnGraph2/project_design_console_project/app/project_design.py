# -*- coding: utf-8 -*-
"""설계 스켈레톤과 설계 요약 실행 코드입니다."""

# 설계 명세를 간결한 데이터 객체로 정의하기 위해 dataclass를 가져옵니다.
from dataclasses import dataclass
# 공통 모듈이 제공하는 데이터 경로를 가져옵니다.
from app.common_bridge import DATA, DOCS


# dataclass 데코레이터를 사용해 설계 명세 클래스를 데이터 중심 객체로 만듭니다.
@dataclass
class AgentSpec:
    """승승장구몰 통합 CS 에이전트의 설계 결정을 보관합니다."""

    # 설계 대상 서비스의 이름을 정의합니다.
    name: str = "승승장구몰 통합 CS 에이전트"
    # 서비스가 사용할 도구 이름을 변경 불가능한 튜플로 정의합니다.
    tools: tuple[str, ...] = (
        "get_order_status",
        "get_stock",
        "search_faq",
        "policy_search",
    )
    # 정책 문서 검색을 위해 RAG가 필요하다는 결정을 기록합니다.
    use_rag: bool = True
    # 같은 대화의 이전 문맥을 유지하기 위해 단기 메모리가 필요함을 기록합니다.
    use_memory: bool = True
    # 도구 수가 적으므로 우선 단일 에이전트로 시작한다는 결정을 기록합니다.
    use_multi_agent: bool = False


def get_order_status(order_id: str) -> str:
    """[R2] 주문번호를 받아 주문 상태 문자열을 반환하도록 설계된 함수입니다."""
    # 이번 강은 구현이 아니라 인터페이스 확정 단계이므로 명시적인 미구현 예외를 냅니다.
    raise NotImplementedError("30강에서 orders.csv 조회 기능을 구현합니다.")


def get_stock(product_name: str) -> str:
    """[R3] 상품명을 받아 재고 상태 문자열을 반환하도록 설계된 함수입니다."""
    # 이후 구현 단계에서 inventory.csv 조회 코드로 교체할 예정임을 표시합니다.
    raise NotImplementedError("30강에서 inventory.csv 조회 기능을 구현합니다.")


def search_faq(keyword: str) -> str:
    """[R4] 검색어를 받아 관련 FAQ 답변을 반환하도록 설계된 함수입니다."""
    # 이후 구현 단계에서 faq.csv 검색 코드로 교체할 예정임을 표시합니다.
    raise NotImplementedError("30강에서 faq.csv 검색 기능을 구현합니다.")


def policy_search(query: str) -> str:
    """[R1] 질문을 받아 정책 문서 검색 근거를 반환하도록 설계된 함수입니다."""
    # 이후 구현 단계에서 문서 임베딩과 검색기 코드로 교체할 예정임을 표시합니다.
    raise NotImplementedError("30강에서 정책 문서 RAG 기능을 구현합니다.")


def build_agent():
    """설정, 도구, RAG, 메모리를 조립할 빌더 인터페이스입니다."""
    # 이번 강에서는 조립 순서와 계약만 확정하고 실제 에이전트는 만들지 않습니다.
    raise NotImplementedError("30강에서 통합 에이전트를 구현합니다.")


def answer(message: str, thread_id: str = "demo") -> str:
    """외부 계층이 호출할 단일 진입점의 최종 인터페이스입니다."""
    # 웹이나 콘솔은 이후 이 함수 하나만 호출하도록 설계합니다.
    raise NotImplementedError("30강에서 에이전트 호출 코드를 구현합니다.")


def print_design() -> None:
    """현재 확정된 설계 내용을 실행 가능한 문서처럼 출력합니다."""
    # 기본 설계 명세 객체를 생성합니다.
    spec = AgentSpec()
    # 출력 구역의 시작을 구분하는 선을 표시합니다.
    print("=" * 68)
    # 설계 대상 서비스 이름을 출력합니다.
    print(f"[설계 스켈레톤] {spec.name}")
    # 제목 영역의 끝을 구분합니다.
    print("=" * 68)
    # 사용자 요구사항을 번호별로 출력합니다.
    print("R1 정책 안내 / R2 주문 상태 / R3 재고 / R4 FAQ / R5 대화 기억")
    # 함수 단위로 분해한 도구 목록을 출력합니다.
    print(f"도구: {', '.join(spec.tools)}")
    # 구성요소 도입 판단을 출력합니다.
    print(f"RAG={spec.use_rag}, 단기 메모리={spec.use_memory}, 멀티에이전트={spec.use_multi_agent}")
    # 외부에서 사용할 단일 함수 계약을 출력합니다.
    print("진입점: answer(message: str, thread_id: str = 'demo') -> str")
    # 원본 common.py가 계산한 데이터 경로를 출력합니다.
    print(f"DATA 경로: {DATA}")
    # 정책 문서 폴더 경로와 존재 여부를 출력합니다.
    print(f"DOCS 경로: {DOCS} / 존재={DOCS.exists()}")
