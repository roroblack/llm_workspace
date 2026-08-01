# -*- coding: utf-8 -*-
"""실제 API 호출 없이 프로젝트 경로·데이터·순수 함수 동작을 검사합니다."""

# 테스트가 프로젝트 루트에서 모듈을 찾도록 pathlib와 sys를 사용합니다.
import pathlib
import sys

# 현재 테스트 파일의 부모의 부모를 프로젝트 루트로 계산합니다.
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
# 프로젝트 루트가 import 경로에 없을 때만 추가합니다.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 테스트할 데이터 로더와 조건부 라우터를 가져옵니다.
from code_app.ai_team import load_competitor_text
from code_app.conditional_review import check, route_after_check


def test_competitor_data_is_loaded() -> None:
    """제공된 CSV가 실제 텍스트로 변환되는지 검사합니다."""
    text = load_competitor_text()
    assert "승승장구몰 경쟁사 현황" in text
    assert "강점=" in text
    assert "약점=" in text


def test_check_marks_short_analysis_as_poor() -> None:
    """짧고 핵심 키워드가 없는 분석을 부실로 판정하는지 검사합니다."""
    state = {"raw": "x", "analysis": "짧은 분석", "report": "", "retries": 0, "verdict": ""}
    assert check(state)["verdict"] == "부실"


def test_router_limits_retry_loop() -> None:
    """재시도 전에는 redo, 상한 도달 후에는 ok를 반환하는지 검사합니다."""
    retry_state = {"raw": "", "analysis": "", "report": "", "retries": 0, "verdict": "부실"}
    stop_state = {"raw": "", "analysis": "", "report": "", "retries": 2, "verdict": "부실"}
    assert route_after_check(retry_state) == "redo"
    assert route_after_check(stop_state) == "ok"
