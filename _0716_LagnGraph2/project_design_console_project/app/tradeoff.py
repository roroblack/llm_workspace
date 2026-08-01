# -*- coding: utf-8 -*-
"""RAG·메모리·멀티에이전트·워크플로우 도입 여부를 규칙으로 판단합니다."""

# 판단 입력을 데이터 객체로 표현하기 위해 dataclass를 가져옵니다.
from dataclasses import dataclass


# 설계 신호를 한 객체로 묶기 위해 dataclass를 적용합니다.
@dataclass
class DesignSpec:
    """구성요소 도입 판단에 필요한 입력 신호입니다."""

    # 프로젝트 이름을 저장합니다.
    name: str = "이름없는 에이전트"
    # 연결할 도구 개수를 저장합니다.
    num_tools: int = 0
    # 검색 대상 사내 문서가 있는지 저장합니다.
    has_internal_docs: bool = False
    # 실시간 데이터 조회가 필요한지 저장합니다.
    needs_realtime: bool = False
    # 여러 턴의 대화 맥락이 필요한지 저장합니다.
    multi_turn: bool = False
    # 분리할 역할의 개수를 저장합니다.
    num_roles: int = 1
    # 세션을 넘어 장기 기억이 필요한지 저장합니다.
    long_running: bool = False


def decide(spec: DesignSpec) -> dict[str, dict[str, object]]:
    """입력 신호를 점수화해 구성요소별 도입 여부와 근거를 반환합니다."""
    # 모든 판단 결과를 저장할 딕셔너리를 생성합니다.
    result: dict[str, dict[str, object]] = {}
    # 사내 문서가 있으면 RAG 점수 2점을 부여합니다.
    rag_score = 2 if spec.has_internal_docs else 0
    # RAG 판단 근거 문장을 구성합니다.
    rag_reason = "사내 문서 근거 검색이 필요" if spec.has_internal_docs else "검색할 고정 문서가 없음"
    # 실시간 데이터가 필요하면 RAG가 아닌 도구 대상이라는 주의를 덧붙입니다.
    if spec.needs_realtime:
        # 기존 근거에 실시간 데이터 처리 원칙을 연결합니다.
        rag_reason += " / 실시간 데이터는 RAG가 아니라 도구로 조회"
    # RAG 판단 결과를 저장합니다.
    result["RAG"] = {"도입": rag_score >= 2, "점수": rag_score, "근거": rag_reason}
    # 멀티턴이면 1점, 장기 누적이면 2점을 더해 메모리 점수를 계산합니다.
    memory_score = (1 if spec.multi_turn else 0) + (2 if spec.long_running else 0)
    # 장기 메모리 판단의 근거를 구성합니다.
    memory_reason = "장기 누적 정보 필요" if spec.long_running else "단기 세션 메모리만으로 충분"
    # 장기 메모리 판단 결과를 저장합니다.
    result["장기메모리"] = {"도입": memory_score >= 2, "점수": memory_score, "근거": memory_reason}
    # 역할이 3개 이상이면 2점, 도구가 8개 이상이면 1점을 부여합니다.
    multi_score = (2 if spec.num_roles >= 3 else 0) + (1 if spec.num_tools >= 8 else 0)
    # 멀티에이전트 판단 근거를 구성합니다.
    multi_reason = f"역할={spec.num_roles}개, 도구={spec.num_tools}개"
    # 멀티에이전트 판단 결과를 저장합니다.
    result["멀티에이전트"] = {"도입": multi_score >= 2, "점수": multi_score, "근거": multi_reason}
    # 역할이 2개 이상이면 정해진 흐름을 그래프로 표현할 가치가 있다고 판단합니다.
    workflow_score = 2 if spec.num_roles >= 2 else 0
    # 워크플로우 판단 결과를 저장합니다.
    result["워크플로우"] = {"도입": workflow_score >= 2, "점수": workflow_score, "근거": f"역할={spec.num_roles}개"}
    # 완성된 전체 판단 결과를 반환합니다.
    return result


def print_decision(spec: DesignSpec) -> None:
    """한 설계 시나리오의 판단 결과를 사람이 읽기 쉽게 출력합니다."""
    # 시나리오 이름을 출력합니다.
    print(f"\n[시나리오] {spec.name}")
    # 판단 결과를 구성요소별로 순회합니다.
    for component, detail in decide(spec).items():
        # 도입 여부를 직관적인 문자열로 변환합니다.
        mark = "도입" if detail["도입"] else "보류"
        # 구성요소명, 판단, 점수, 근거를 한 줄로 출력합니다.
        print(f"- {component}: {mark} / 점수={detail['점수']} / {detail['근거']}")


def run_examples() -> None:
    """HTML 설명의 판단 기준을 서로 다른 세 시나리오로 실행 확인합니다."""
    # 통합 CS 에이전트 시나리오를 정의합니다.
    cs = DesignSpec("통합 CS 에이전트", 4, True, True, True, 1, False)
    # 보고서 작성 AI 팀 시나리오를 정의합니다.
    team = DesignSpec("보고서 작성 AI 팀", 2, True, False, False, 3, False)
    # 단순 FAQ 봇 시나리오를 정의합니다.
    faq = DesignSpec("단순 FAQ 봇", 1, False, False, False, 1, False)
    # 준비한 시나리오를 순서대로 출력합니다.
    for spec in (cs, team, faq):
        # 각 시나리오의 판단 결과를 출력합니다.
        print_decision(spec)
