# -*- coding: utf-8 -*-
"""외부 API 호출 없이 순수 규칙과 LangGraph 워크플로우를 테스트합니다."""

# 테스트 대상 코드 폴더를 import 경로에 추가하기 위해 sys와 pathlib을 가져옵니다.
import pathlib
import sys

# 프로젝트 루트/code 폴더를 파이썬 모듈 검색 경로 앞쪽에 추가합니다.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "code"))

# 테스트할 순수 규칙 함수들을 가져옵니다.
from rules import calculate_priority, calculate_route, calculate_team, normalize_category

# 조건 분기와 노드 예외 처리 결과를 검증할 워크플로우 기능을 가져옵니다.
import workflow as workflow_module
from workflow import assign_node, build_conditional_workflow, priority_node


class StaticLLM:
    """항상 지정된 카테고리를 반환하여 외부 API 호출을 없애는 테스트 모델입니다."""

    def __init__(self, category: str) -> None:
        self.category = category

    def invoke(self, messages):
        return self.category


class FailingLLM:
    """classify_node의 try/except 검증을 위해 항상 예외를 던지는 테스트 모델입니다."""

    def invoke(self, messages):
        raise RuntimeError("의도적인 분류 실패")


def test_normalize_category_exact_match() -> None:
    """정확한 카테고리 출력은 오류 없이 그대로 채택되어야 합니다."""

    # 정확히 결제라고 입력했을 때 결제와 빈 오류 문자열이 반환되는지 확인합니다.
    assert normalize_category("결제") == ("결제", "")


def test_normalize_category_sentence_match() -> None:
    """설명 문장 안의 허용 카테고리도 추출되어야 합니다."""

    # 문장형 응답에서도 기술지원이라는 허용 단어를 찾아야 합니다.
    assert normalize_category("이 문의는 기술지원으로 보입니다.") == ("기술지원", "")


def test_normalize_category_fallback() -> None:
    """허용 목록 밖 출력은 기타로 보정되고 오류가 기록되어야 합니다."""

    # 허용되지 않은 단어를 입력하여 폴백 결과를 받습니다.
    category, error = normalize_category("제품문의")

    # 안전한 기본 카테고리는 기타여야 합니다.
    assert category == "기타"

    # 보정 이유를 추적할 수 있는 오류 메시지가 있어야 합니다.
    assert "미허용" in error


def test_priority_and_assignment_rules() -> None:
    """결제 티켓은 긴급 우선순위와 결제지원팀으로 처리되어야 합니다."""

    # 결제 오류 문장이 긴급으로 판정되는지 확인합니다.
    assert calculate_priority("결제 오류가 발생합니다.", "결제") == "긴급"

    # 결제 카테고리가 결제지원팀으로 배정되는지 확인합니다.
    assert calculate_team("결제") == "결제지원팀"


def test_conditional_router() -> None:
    """긴급은 notify, 보통은 assign 경로를 반환해야 합니다."""

    # 긴급 상태가 즉시 알림 경로를 선택하는지 확인합니다.
    assert calculate_route("긴급") == "notify"

    # 보통 상태가 일반 배정 경로를 선택하는지 확인합니다.
    assert calculate_route("보통") == "assign"


def test_conditional_workflow_alerts_only_urgent_tickets() -> None:
    """긴급 티켓만 notify를 거쳐 즉시알림 값을 가져야 합니다."""

    urgent_workflow = build_conditional_workflow("test", llm=StaticLLM("결제"))
    normal_workflow = build_conditional_workflow("test", llm=StaticLLM("회원"))

    urgent_result = urgent_workflow.invoke({"content": "결제가 안 돼요."})
    normal_result = normal_workflow.invoke({"content": "회원 정보를 바꾸고 싶어요."})

    assert urgent_result["priority"] == "긴급"
    assert urgent_result["alert"] == "즉시알림"
    assert urgent_result["team"] == "결제지원팀"
    assert normal_result["priority"] == "보통"
    assert "alert" not in normal_result
    assert normal_result["team"] == "회원관리팀"


def test_classify_exception_is_assigned_to_review_team() -> None:
    """분류 노드 예외는 상태에 기록되고 마지막 팀은 검토필요여야 합니다."""

    workflow = build_conditional_workflow("test", llm=FailingLLM())

    result = workflow.invoke({"content": "일반 문의입니다."})

    assert result["category"] == "기타"
    assert "classify 노드 예외" in result["error"]
    assert "의도적인 분류 실패" in result["error"]
    assert result["team"] == "검토필요"


def test_priority_exception_is_preserved_for_final_assignment(monkeypatch) -> None:
    """우선순위 계산 실패도 기본값으로 흐름을 계속한 뒤 검토필요로 배정해야 합니다."""

    def raise_priority_error(content: str, category: str) -> str:
        raise ValueError("우선순위 규칙 실패")

    monkeypatch.setattr(workflow_module, "calculate_priority", raise_priority_error)
    state = {"content": "문의", "category": "회원"}
    state.update(priority_node(state))
    state.update(assign_node(state))

    assert state["priority"] == "보통"
    assert "priority 노드 예외" in state["error"]
    assert state["team"] == "검토필요"


def test_assign_exception_records_error_and_review_team(monkeypatch) -> None:
    """마지막 배정 노드 자체가 실패해도 검토필요 팀과 오류를 반환해야 합니다."""

    def raise_team_error(category: str) -> str:
        raise LookupError("팀 규칙 실패")

    monkeypatch.setattr(workflow_module, "calculate_team", raise_team_error)

    result = assign_node({"content": "문의", "category": "회원"})

    assert result["team"] == "검토필요"
    assert "assign 노드 예외" in result["error"]
