# -*- coding: utf-8 -*-
"""실습문제 1: Planner → Worker 뒤에 Reviewer를 추가합니다."""

# provider별 모델 생성 함수를 가져옵니다.
from app.common import get_chat
# 기존 계획, 실행, 취합 함수를 재사용합니다.
from app.role_agent import combine_report, plan, work

# Reviewer가 새 실행안을 만들지 않고 누락과 개선점만 제시하도록 지시합니다.
REVIEWER_SYSTEM = (
    "너는 마케팅 캠페인 검토자(Reviewer)다. "
    "실행안 전체를 읽고 누락되었거나 보완할 점을 구체적으로 3가지 이상 제시하라. "
    "새 실행안을 작성하지 말고 검토 의견만 작성하라."
)

def review(llm, report: str, reviewer_prompt: str = REVIEWER_SYSTEM) -> str:
    """완성된 실행안 전체를 검토해 개선 의견을 반환합니다."""
    # 메시지 클래스를 실제 검토 호출 시점에만 가져옵니다.
    from langchain_core.messages import HumanMessage, SystemMessage
    # Reviewer 역할 지시와 검토 대상 보고서를 모델에 전달합니다.
    result = llm.invoke([SystemMessage(reviewer_prompt), HumanMessage(f"[검토할 캠페인 실행안]\n{report}")])
    # 응답 본문을 문자열로 반환합니다.
    return str(result.content)

def run_campaign_with_review(provider: str, brief_text: str) -> str:
    """계획, 실행, 취합, 검토의 네 단계를 순서대로 수행합니다."""
    # 계획용 모델을 재현성이 높은 설정으로 생성합니다.
    llm_plan = get_chat(provider=provider, temperature=0.0)
    # 실행용 모델을 약간 창의적인 설정으로 생성합니다.
    llm_work = get_chat(provider=provider, temperature=0.5)
    # 검토용 모델을 일관성이 높은 설정으로 생성합니다.
    llm_review = get_chat(provider=provider, temperature=0.0)
    # Planner로 하위 작업을 생성합니다.
    subtasks = plan(llm_plan, brief_text)
    # 각 하위 작업을 Worker로 실행해 튜플 리스트로 저장합니다.
    outputs = [(subtask, work(llm_work, brief_text, subtask)) for subtask in subtasks]
    # Worker 결과를 하나의 보고서로 취합합니다.
    report = combine_report(brief_text, outputs)
    # 취합된 전체 보고서를 Reviewer에게 전달합니다.
    opinion = review(llm_review, report)
    # 원본 보고서 끝에 검토 의견 섹션을 붙여 반환합니다.
    return report + f"\n## 검토 의견\n{opinion}\n"
