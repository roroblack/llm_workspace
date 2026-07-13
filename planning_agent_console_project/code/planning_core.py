# -*- coding: utf-8 -*-
"""Plan-and-Execute 실습의 핵심 로직을 모아 둔 모듈입니다."""

# pathlib는 CSV 파일 경로를 안전하게 계산하기 위해 사용합니다.
from pathlib import Path

# pandas는 project_tasks.csv 파일을 읽고 필터링하기 위해 사용합니다.
import pandas as pd

# BaseModel과 Field는 LLM 출력 구조를 명확하게 정의하기 위해 사용합니다.
from pydantic import BaseModel, Field

# get_chat은 common.py에서 제공하는 LangChain ChatModel 생성 함수입니다.
from common import get_chat


# 프로젝트 루트 경로를 계산합니다.
ROOT = Path(__file__).resolve().parent.parent

# 데이터 폴더 경로를 계산합니다.
DATA = ROOT / "data"

# 계획 단계의 최소 개수입니다.
MIN_STEPS = 2

# 계획 단계의 최대 개수입니다.
MAX_STEPS = 8


class Plan(BaseModel):
    """목표를 실행 가능한 하위 작업으로 분해한 결과입니다."""

    # goal은 사용자가 입력한 원래 목표를 저장합니다.
    goal: str = Field(description="원래 목표")

    # steps는 실행 순서대로 정리된 하위 작업 목록을 저장합니다.
    steps: list[str] = Field(description="순서대로 실행할 하위 작업 목록")


def make_fallback_plan(goal: str) -> Plan:
    """API 키가 없어도 실습 확인이 가능하도록 규칙 기반 계획을 생성합니다."""
    # 목표 문자열에 맞춘 기본 단계 목록을 작성합니다.
    steps = [
        "목표와 성공 기준을 명확히 정의한다.",
        "시장·고객·경쟁 상황을 조사한다.",
        "상품 또는 캠페인 콘셉트와 실행 범위를 확정한다.",
        "필요한 리소스와 담당 팀을 배정한다.",
        "실행 일정을 세우고 핵심 작업을 진행한다.",
        "결과를 측정하고 개선 사항을 정리한다.",
    ]

    # Plan 객체를 생성해 반환합니다.
    return Plan(goal=goal, steps=steps)


def make_plan(provider: str, goal: str, max_tokens: int | None = None) -> Plan:
    """LLM 구조화 출력으로 목표를 Plan 객체로 분해합니다."""
    # get_chat은 common.py의 공통 함수를 사용하여 provider별 LangChain 모델을 만듭니다.
    llm = get_chat(provider=provider, temperature=0, max_tokens=max_tokens)

    # with_structured_output은 LLM 응답을 Pydantic Plan 스키마에 맞게 받도록 합니다.
    planner = llm.with_structured_output(Plan)

    # 모델에게 프로젝트 매니저 역할과 단계 개수 조건을 명확히 전달합니다.
    prompt = (
        "너는 승승장구몰의 프로젝트 매니저다. "
        f"다음 목표를 실행 순서대로 {MIN_STEPS}~{MAX_STEPS}개의 구체적 하위 작업으로 분해하라.\n"
        "Return only data that matches the requested schema. Keep each step concise.\n"
        f"목표: {goal}"
    )

    # 구조화 출력 결과를 Plan 객체로 반환합니다.
    return planner.invoke(prompt)


def validate_plan(plan: Plan) -> tuple[bool, str]:
    """계획이 실행 가능한지 검사하고 적합 여부와 사유를 반환합니다."""
    # 계획 단계 개수를 계산합니다.
    step_count = len(plan.steps)

    # 단계가 너무 적으면 목표 분해가 부족하다고 판단합니다.
    if step_count < MIN_STEPS:
        return False, f"단계가 {step_count}개뿐입니다. 최소 {MIN_STEPS}개 이상 필요합니다."

    # 단계가 너무 많으면 과분해로 판단합니다.
    if step_count > MAX_STEPS:
        return False, f"단계가 {step_count}개입니다. 최대 {MAX_STEPS}개 이하가 적절합니다."

    # 빈 문자열 단계가 있는지 검사합니다.
    if any(not step.strip() for step in plan.steps):
        return False, "빈 단계가 포함되어 있습니다. 실행 가능한 문장으로 작성해야 합니다."

    # 모든 조건을 통과하면 적합한 계획으로 판단합니다.
    return True, "적합한 계획입니다."


def replan(provider: str, goal: str, reason: str, max_tokens: int | None = None) -> Plan:
    """검증 실패 사유를 피드백으로 전달하여 계획을 다시 생성합니다."""
    # provider에 맞는 LangChain ChatModel을 생성합니다.
    llm = get_chat(provider=provider, temperature=0, max_tokens=max_tokens)

    # Plan 스키마로 구조화 출력이 나오도록 설정합니다.
    planner = llm.with_structured_output(Plan)

    # 실패 사유를 명시하여 같은 문제가 반복되지 않도록 프롬프트를 구성합니다.
    prompt = (
        "너는 승승장구몰의 프로젝트 매니저다. 이전 계획은 아래 이유로 부적합했다.\n"
        f"부적합 사유: {reason}\n"
        f"이 문제를 반드시 고쳐서 {MIN_STEPS}~{MAX_STEPS}개의 구체적인 하위 작업으로 다시 분해하라.\n"
        "Return only data that matches the requested schema. Keep each step concise.\n"
        f"목표: {goal}"
    )

    # 재계획 결과를 Plan 객체로 반환합니다.
    return planner.invoke(prompt)


def plan_with_validation(provider: str, goal: str, max_replan: int = 2, max_tokens: int | None = None) -> Plan:
    """계획 생성 후 검증하고, 부적합하면 정해진 횟수만큼 재계획합니다."""
    # 첫 계획을 생성합니다.
    plan = make_plan(provider, goal, max_tokens=max_tokens)

    # 최대 재계획 횟수만큼 검증과 재계획을 반복합니다.
    for attempt in range(1, max_replan + 1):
        # 현재 계획을 검증합니다.
        ok, reason = validate_plan(plan)

        # 검증 결과를 콘솔에 출력합니다.
        print(f"[검증 {attempt}] {'적합' if ok else '부적합'} - {reason}")

        # 적합하면 현재 계획을 그대로 반환합니다.
        if ok:
            return plan

        # 부적합하면 실패 사유를 넣어 재계획합니다.
        plan = replan(provider, goal, reason, max_tokens=max_tokens)

    # 재계획 횟수를 모두 사용한 뒤 마지막 계획을 반환합니다.
    return plan


def list_tasks(status: str = "전체") -> str:
    """신상품 출시 프로젝트의 작업 목록을 상태별로 조회합니다."""
    # CSV 파일을 DataFrame으로 읽습니다.
    tasks_df = pd.read_csv(DATA / "project_tasks.csv")

    # status가 전체가 아니면 해당 상태의 행만 필터링합니다.
    if status != "전체":
        tasks_df = tasks_df[tasks_df["status"] == status]

    # 필터링 결과가 비어 있으면 안내 문장을 반환합니다.
    if tasks_df.empty:
        return f"'{status}' 상태인 작업이 없습니다."

    # 각 작업 행을 사람이 읽기 쉬운 문자열로 변환합니다.
    lines = [
        f"- [{row.status}] {row.task_id} {row.task_name} (담당:{row.team}, 마감:{row.due_date})"
        for row in tasks_df.itertuples(index=False)
    ]

    # 줄바꿈으로 연결해 하나의 문자열로 반환합니다.
    return "\n".join(lines)


def recommend_next_task_without_llm() -> str:
    """LLM 없이 대기 작업 중 마감일이 가장 빠른 작업을 추천합니다."""
    # 프로젝트 작업 CSV를 읽습니다.
    tasks_df = pd.read_csv(DATA / "project_tasks.csv")

    # 대기 상태의 작업만 필터링하고 마감일 기준으로 정렬합니다.
    waiting = tasks_df[tasks_df["status"] == "대기"].sort_values("due_date")

    # 대기 작업이 없다면 안내 메시지를 반환합니다.
    if waiting.empty:
        return "현재 대기 상태인 작업이 없습니다."

    # 가장 먼저 처리해야 할 작업 1개를 가져옵니다.
    row = waiting.iloc[0]

    # 추천 문장을 반환합니다.
    return f"가장 먼저 시작할 작업은 {row['task_id']} {row['task_name']}입니다. 담당은 {row['team']}, 마감일은 {row['due_date']}입니다."


def print_plan(plan: Plan) -> None:
    """Plan 객체를 콘솔에 보기 좋게 출력합니다."""
    # 목표를 출력합니다.
    print(f"목표: {plan.goal}")

    # 단계 목록을 번호와 함께 출력합니다.
    for index, step in enumerate(plan.steps, start=1):
        print(f"  {index}. {step}")
