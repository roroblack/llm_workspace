# -*- coding: utf-8 -*-
"""Worker 실패 시 재시도하고 부분 실패를 허용하는 실습 코드입니다."""

# 공통 모델 생성 함수를 가져옵니다.
from app.common import get_chat
# 핵심 Planner/Worker/취합 함수를 재사용합니다.
from app.role_agent import combine_report, plan, work

# 최초 호출 이후 허용할 추가 재시도 횟수를 2회로 지정합니다.
MAX_RETRY = 2

def work_with_retry(llm, brief_text: str, subtask: str, index: int, total: int, force_fail: bool = False) -> tuple[bool, str]:
    """Worker를 최대 3회 시도하고 성공 여부와 결과를 반환합니다."""
    # 최초 1회와 재시도 2회를 합친 총 3회를 순회합니다.
    for attempt in range(1, MAX_RETRY + 2):
        try:
            # 작업 번호와 현재 시도 횟수를 출력합니다.
            print(f"작업 {index}/{total}, 시도 {attempt}/{MAX_RETRY + 1}")
            # 메뉴 시연에서 선택한 작업은 실제 API 호출 전에 모의 오류를 발생시킵니다.
            if force_fail:
                raise TimeoutError("재시도 동작 확인을 위한 모의 오류")
            # 모의 실패 대상이 아니면 실제 Worker를 호출합니다.
            return True, work(llm, brief_text, subtask)
        except Exception as error:
            # 오류 형식과 메시지를 기록합니다.
            error_text = f"{type(error).__name__}: {error}"
            # 현재 오류를 사용자에게 출력합니다.
            print(f"  실패: {error_text}")
            # 마지막 시도가 아니면 다음 반복에서 재시도합니다.
            if attempt <= MAX_RETRY:
                print("  재시도합니다.")
            else:
                # 모든 시도가 실패하면 False와 오류 문자열을 반환합니다.
                return False, error_text
    # 논리상 도달하지 않지만 타입 검사기를 위해 기본 실패값을 반환합니다.
    return False, "알 수 없는 오류"

def run_campaign_robust(provider: str, brief_text: str, fail_indices: set[int] | None = None) -> str:
    """실패 작업을 기록하고 나머지 작업을 끝까지 실행합니다."""
    # 전달값이 없으면 빈 집합으로 바꾸어 포함 여부 검사를 단순화합니다.
    fail_indices = fail_indices or set()
    # 계획용 모델을 생성합니다.
    llm_plan = get_chat(provider=provider, temperature=0.0)
    # 실행용 모델을 생성합니다.
    llm_work = get_chat(provider=provider, temperature=0.5)
    # Planner로 작업 목록을 생성합니다.
    subtasks = plan(llm_plan, brief_text)
    # 성공한 작업 결과를 저장할 리스트를 만듭니다.
    outputs: list[tuple[str, str]] = []
    # 실패한 작업 정보를 저장할 리스트를 만듭니다.
    failed: list[tuple[int, str, str]] = []
    # 모든 하위 작업을 순회합니다.
    for index, subtask in enumerate(subtasks, start=1):
        # 선택한 작업 번호이면 force_fail을 True로 전달합니다.
        ok, information = work_with_retry(llm_work, brief_text, subtask, index, len(subtasks), index in fail_indices)
        # 성공 여부에 따라 결과 저장 위치를 나눕니다.
        if ok:
            outputs.append((subtask, information))
        else:
            failed.append((index, subtask, information))
    # 성공한 결과를 기본 보고서로 취합합니다.
    report = combine_report(brief_text, outputs)
    # 실패 작업이 있으면 미완료 섹션을 추가합니다.
    if failed:
        report += "\n## 미완료 작업\n"
        # 실패한 각 작업의 번호, 내용, 오류를 한 줄씩 추가합니다.
        for index, subtask, error in failed:
            report += f"- 원래 작업 {index}: {subtask} — {error}\n"
    # 부분 성공 결과와 실패 기록을 포함한 보고서를 반환합니다.
    return report
