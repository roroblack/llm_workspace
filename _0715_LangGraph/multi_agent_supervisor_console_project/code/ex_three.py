# -*- coding: utf-8 -*-
"""문제 1 — 경쟁사 분석가 에이전트 추가 (3-way 라우팅).

기존 모듈(router/agents/supervisor/data_repository)을 재사용하여
sales·policy에 competitor 축을 더한 3-way Supervisor 데모를 구성합니다.

- @tool search_competitor(): data/competitor_data.csv를 조회하는 LangChain 도구
- route_rule_3way / route_llm_3way: "sales" / "policy" / "competitor" 3개 라벨 반환
- ThreeWaySupervisor: 3개 전문 에이전트 중 알맞은 하나에 위임

라우팅과 경쟁사 도구 실행은 API 키 없이 동작합니다.
최종 답변 생성만 선택한 공급자의 API 키가 필요하며, 키가 없으면
common.require_key가 명시적 오류를 발생시킵니다(폴백·데모모드 없음).
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any

# 직접 실행(python code/ex_three.py)과 모듈 실행 모두에서 code 폴더를 찾도록 경로를 보정합니다.
CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

# LangChain 도구 데코레이터를 가져옵니다.
from langchain_core.tools import tool

# 공통 데이터 경로를 가져옵니다.
from common import DATA
# 범용 전문 에이전트 클래스와 기존 2개 에이전트 빌더를 재사용합니다.
from agents import SpecialistAgent, build_specialists
# 기존 규칙 라우터 키워드와 결정 객체, LLM 응답 유틸을 재사용합니다.
from router import POLICY_WORDS, SALES_WORDS, RouteDecision, build_router_llm
from message_utils import extract_text

# 경쟁사 비교 의도를 빠르게 포착하기 위한 키워드 튜플입니다.
COMPETITOR_WORDS: tuple[str, ...] = (
    "경쟁사",
    "경쟁",
    "비교",
    "타사",
    "다른 곳",
    "다른곳",
    "가격비교",
    "대비",
    "라이벌",
    "vs",
)


# --------------------------------------------------------------------------- #
# 경쟁사 조회 도구
# --------------------------------------------------------------------------- #
def _load_competitors() -> list[dict[str, str]]:
    """competitor_data.csv를 읽어 행 딕셔너리 목록으로 반환합니다."""
    # common.py의 DATA 경로를 기준으로 경쟁사 CSV 경로를 구성합니다.
    path = DATA / "competitor_data.csv"

    # 데이터 파일이 없으면 원인을 알 수 있는 명시적 오류를 발생시킵니다(폴백 없음).
    if not path.is_file():
        raise FileNotFoundError(f"경쟁사 데이터 파일을 찾을 수 없습니다: {path}")

    # BOM이 있는 CSV도 안전하게 읽도록 utf-8-sig로 파일을 엽니다.
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        # 열 이름을 키로 사용하는 DictReader로 모든 행을 읽습니다.
        return list(csv.DictReader(file))


@tool
def search_competitor(query: str) -> str:
    """경쟁사 비교 데이터(competitor_data.csv)에서 회사명·카테고리로 경쟁 구도를 조회한다."""
    # 검색어 앞뒤 공백을 제거하고 소문자로 정규화합니다.
    normalized = query.strip().lower()

    # 전체 경쟁사 데이터를 읽습니다.
    rows = _load_competitors()

    # 회사명 또는 주력 카테고리가 검색어와 서로 포함 관계인 행만 선택합니다.
    matched = [
        row
        for row in rows
        if normalized
        and (
            normalized in row["company"].lower()
            or normalized in row["main_category"].lower()
            or row["main_category"].lower() in normalized
            or row["company"].lower() in normalized
        )
    ]

    # 일반적인 비교 질문이라 특정 회사·카테고리가 없으면 전체 경쟁 구도를 근거로 사용합니다.
    if not matched:
        matched = rows

    # 관련 데이터가 전혀 없으면 명확한 안내 문장을 반환합니다.
    if not matched:
        return "경쟁사 비교 데이터를 찾지 못했습니다."

    # 사람이 읽기 쉬운 비교 근거 문자열을 구성합니다.
    lines = ["[경쟁사 비교 데이터]"]
    for row in matched:
        # 승승장구몰은 자사, 나머지는 경쟁사로 태그를 붙여 비교 관점을 명확히 합니다.
        tag = "자사" if row["company"] == "승승장구몰" else "경쟁사"
        lines.append(
            f"- ({tag}) {row['company']} | 주력:{row['main_category']} | "
            f"평점 {row['rating']} | 강점:{row['strength']} | 약점:{row['weakness']}"
        )

    # 여러 줄을 결합하여 도구 결과로 반환합니다.
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# 3-way 라우터 (sales / policy / competitor)
# --------------------------------------------------------------------------- #
def route_rule_3way(question: str) -> RouteDecision:
    """키워드만으로 competitor / policy / sales 3개 라벨로 분류합니다.

    경쟁 비교 의도를 먼저 포착하기 위해 competitor → policy → sales 순으로 검사합니다.
    """
    # 입력 질문의 앞뒤 공백을 제거합니다.
    normalized = question.strip()

    # 경쟁사 키워드를 먼저 검사하여 비교 질문을 우선 포착합니다.
    competitor_hits = [word for word in COMPETITOR_WORDS if word in normalized]
    if competitor_hits:
        return RouteDecision(
            target="competitor",
            method="rule",
            reason=f"경쟁 키워드 감지: {', '.join(competitor_hits)}",
            llm_calls=0,
        )

    # 정책 키워드를 검사합니다.
    policy_hits = [word for word in POLICY_WORDS if word in normalized]
    if policy_hits:
        return RouteDecision(
            target="policy",
            method="rule",
            reason=f"정책 키워드 감지: {', '.join(policy_hits)}",
            llm_calls=0,
        )

    # 추천 키워드를 검사합니다.
    sales_hits = [word for word in SALES_WORDS if word in normalized]
    if sales_hits:
        return RouteDecision(
            target="sales",
            method="rule",
            reason=f"추천 키워드 감지: {', '.join(sales_hits)}",
            llm_calls=0,
        )

    # 어느 축도 명확하지 않으면 애매함을 나타내는 unknown을 반환합니다.
    return RouteDecision(
        target="unknown",
        method="rule",
        reason="명시적인 경쟁/정책/추천 키워드를 찾지 못함",
        llm_calls=0,
    )


def route_llm_3way(llm: Any, question: str) -> RouteDecision:
    """LLM의 의미 이해로 질문을 competitor / policy / sales 3개 라벨로 분류합니다."""
    # 출력 형식을 세 라벨로 제한하는 분류 프롬프트를 구성합니다.
    prompt = (
        "고객 질문을 다음 세 라벨 중 하나로 분류하라.\n"
        "- competitor: 경쟁사·타사와의 비교, 자사 대비 강점/약점, 경쟁 구도 문의\n"
        "- policy: 환불, 취소, 반품, 교환, 배송 기간, 적립, 회원 정책 문의\n"
        "- sales: 상품 선택, 추천, 가격대, 카테고리, 인기 상품 문의\n"
        "반드시 competitor, policy, sales 중 한 단어만 출력한다.\n"
        f"질문: {question}\n"
        "라벨:"
    )

    # 분류 전용 LLM을 한 번 호출합니다.
    response = llm.invoke(prompt)

    # 응답을 소문자 문자열로 변환합니다.
    answer = extract_text(response).lower()

    # 응답에 포함된 라벨을 순서대로 확인하여 대상을 결정합니다.
    if "competitor" in answer:
        target = "competitor"
    elif "policy" in answer:
        target = "policy"
    else:
        # 그 외에는 안전한 기본 라벨인 sales로 정규화합니다.
        target = "sales"

    # 호출 횟수 1회와 원본 분류 응답을 설명에 포함해 반환합니다.
    return RouteDecision(
        target=target,
        method="llm",
        reason=f"LLM 분류 응답: {answer!r}",
        llm_calls=1,
    )


# --------------------------------------------------------------------------- #
# 3-way Supervisor
# --------------------------------------------------------------------------- #
def build_competitor_agent(provider: str) -> SpecialistAgent:
    """경쟁사 분석만 담당하는 competitor 전문 에이전트를 생성합니다."""
    # @tool 객체는 .invoke로 실행하므로 SpecialistAgent가 요구하는 함수 형태로 감쌉니다.
    return SpecialistAgent(
        name="competitor",
        role_prompt=(
            "승승장구몰의 경쟁사 분석 전문 상담원이다. 경쟁사 비교 데이터를 근거로 "
            "자사와 경쟁사의 강점·약점·평점을 객관적으로 비교하고, 근거 밖 추측은 하지 않는다."
        ),
        tool_name="search_competitor",
        tool_function=lambda keyword: search_competitor.invoke(keyword),
        provider=provider,
    )


class ThreeWaySupervisor:
    """질문을 분류하여 sales / policy / competitor 세 에이전트 중 하나에 위임합니다."""

    def __init__(self, provider: str) -> None:
        # 라우팅에 사용할 LLM을 생성합니다.
        self.router_llm = build_router_llm(provider)

        # 기존 빌더로 sales·policy 에이전트를, 신규 빌더로 competitor 에이전트를 생성합니다.
        sales_agent, policy_agent = build_specialists(provider)
        competitor_agent = build_competitor_agent(provider)

        # 라우팅 대상 문자열로 에이전트를 바로 찾도록 딕셔너리를 구성합니다.
        self.agents: dict[str, SpecialistAgent] = {
            "sales": sales_agent,
            "policy": policy_agent,
            "competitor": competitor_agent,
        }

    def decide(self, question: str, mode: str = "hybrid") -> RouteDecision:
        """선택한 모드로 3-way 라우팅 결정을 생성합니다."""
        # 규칙 모드: 키워드 라우터만 사용하고, 애매하면 기본 대상 sales로 보냅니다.
        if mode == "rule":
            decision = route_rule_3way(question)
            if decision.target == "unknown":
                return RouteDecision(
                    target="sales",
                    method="rule-default",
                    reason=f"{decision.reason}; 기본 대상 sales 적용",
                    llm_calls=0,
                )
            return decision

        # LLM 모드: 모든 질문을 LLM으로 분류합니다.
        if mode == "llm":
            return route_llm_3way(self.router_llm, question)

        # 하이브리드 모드: 규칙 우선, 애매할 때만 LLM을 호출합니다.
        if mode == "hybrid":
            rule_decision = route_rule_3way(question)
            if rule_decision.target != "unknown":
                return RouteDecision(
                    target=rule_decision.target,
                    method="hybrid-rule",
                    reason=rule_decision.reason,
                    llm_calls=0,
                )
            llm_decision = route_llm_3way(self.router_llm, question)
            return RouteDecision(
                target=llm_decision.target,
                method="hybrid-llm",
                reason=f"규칙 판단 불가 → {llm_decision.reason}",
                llm_calls=llm_decision.llm_calls,
            )

        # 허용하지 않은 모드는 즉시 오류로 처리합니다.
        raise ValueError(f"지원하지 않는 라우터 모드입니다: {mode}")

    def run(self, question: str, mode: str = "hybrid"):
        """라우팅 결정을 내리고 선택된 전문 에이전트에 위임합니다."""
        # 빈 질문은 LLM 호출 전에 차단합니다.
        if not question.strip():
            raise ValueError("질문이 비어 있습니다. 내용을 입력해 주세요.")

        # 담당 에이전트를 결정합니다.
        decision = self.decide(question, mode)

        # Supervisor 판단 과정을 로그로 출력합니다.
        print(f"[Supervisor] 질문 수신: {question!r}")
        print(f"[Supervisor] 라우팅 결정: {decision.target} ({decision.method}) - {decision.reason}")
        print(f"[Supervisor] 위임 → {decision.target} 전문 에이전트")

        # 결정된 대상 에이전트를 가져와 질문을 그대로 위임합니다.
        agent = self.agents[decision.target]
        result = agent.run(question)

        # 위임 결과를 반환합니다.
        return decision, result


# --------------------------------------------------------------------------- #
# 데모 실행
# --------------------------------------------------------------------------- #
# 세 에이전트를 고르게 자극하는 라우팅 예시 질문입니다.
DEMO_QUESTIONS: tuple[str, ...] = (
    "경쟁사랑 비교하면 어때?",
    "환불은 며칠 안에 신청해야 해?",
    "전자기기 추천 좀 해줘",
)

# 문제 지문이 요구한 기대 입력입니다.
EXPECTED_QUESTION = "경쟁사랑 비교하면 어때?"

# 이 데모에서 사용할 기본 LLM 공급자입니다.
CURRENT_PROVIDER = "gemini"

# 공급자별 필수 API 키 환경변수 이름입니다.
PROVIDER_KEY_ENV: dict[str, str] = {
    "gemini": "GOOGLE_API_KEY",
    "openai": "OPENAI_API_KEY",
}


def demo_routing_offline() -> None:
    """API 키 없이 규칙 라우터의 3-way 분류만 시연합니다."""
    print("=" * 70)
    print("[1] 규칙 라우터 3-way 분류 (API 키 불필요)")
    print("=" * 70)
    for question in DEMO_QUESTIONS:
        decision = route_rule_3way(question)
        print(f"- {question} → {decision.target} ({decision.reason})")


def demo_competitor_tool_offline() -> None:
    """API 키 없이 경쟁사 조회 도구 자체의 동작을 시연합니다."""
    print("\n" + "=" * 70)
    print("[2] @tool search_competitor 단독 실행 (API 키 불필요)")
    print("=" * 70)
    # @tool 객체이므로 .invoke로 실행합니다.
    print(search_competitor.invoke("경쟁사"))


def demo_end_to_end() -> None:
    """기대 질문을 3-way Supervisor에 통과시켜 위임과 답변까지 시연합니다."""
    import os

    print("\n" + "=" * 70)
    print("[3] 3-way Supervisor 위임 + 경쟁사 답변 생성")
    print("=" * 70)

    # 최종 답변 생성은 LLM 호출이 필요하므로 키 존재 여부를 먼저 확인합니다.
    key_env = PROVIDER_KEY_ENV[CURRENT_PROVIDER]
    if not os.getenv(key_env):
        # 키가 없으면 가짜 답변을 만들지 않고 필요한 조건을 정직하게 안내합니다.
        print(f"[안내] 최종 답변 생성 단계는 {key_env}가 필요합니다.")
        print("       .env에 키를 채우면 competitor 에이전트의 실제 답변까지 실행됩니다.")
        print("       (라우팅·도구 근거는 위 [1][2]에서 키 없이 확인 완료)")
        return

    # 키가 있으면 실제 3-way Supervisor를 구성하고 기대 질문을 실행합니다.
    supervisor = ThreeWaySupervisor(CURRENT_PROVIDER)
    decision, result = supervisor.run(EXPECTED_QUESTION, mode="hybrid")

    # 위임된 competitor 에이전트의 근거와 최종 답변을 출력합니다.
    print(f"\n[{result.agent_name}] 사용 도구: {result.tool_name}")
    print(f"[{result.agent_name}] 도구 입력: {result.tool_input}")
    print(f"\n[도구 근거]\n{result.evidence}")
    print(f"\n[최종 답변]\n{result.answer}")


def main() -> None:
    """세 단계로 3-way 경쟁사 라우팅을 시연합니다."""
    print("문제 1 — 경쟁사 분석가 에이전트 추가 (3-way 라우팅) 데모")
    demo_routing_offline()
    demo_competitor_tool_offline()
    demo_end_to_end()


if __name__ == "__main__":
    main()
