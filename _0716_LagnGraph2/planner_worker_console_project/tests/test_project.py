# -*- coding: utf-8 -*-
"""API 호출 없이 데이터, 취합, YAML 설정을 검증하는 테스트입니다."""

# 핵심 데이터 로드 및 취합 함수를 가져옵니다.
from app.role_agent import combine_report, load_brief_text, load_campaign_table
# YAML 프롬프트 로드 함수를 가져옵니다.
from app.yaml_exercise import load_prompts

def test_campaign_data_is_available() -> None:
    # 캠페인 표가 비어 있지 않은지 검증합니다.
    assert not load_campaign_table().empty

def test_brief_contains_expected_fields() -> None:
    # CMP02 브리프에 주요 필드 이름이 모두 포함되는지 검증합니다.
    brief = load_brief_text("CMP02")
    # 사람이 읽는 브리프에 캠페인명, 타깃, 예산이 포함되어야 합니다.
    assert "캠페인명:" in brief and "타깃:" in brief and "예산:" in brief

def test_combine_report_builds_sections() -> None:
    # 두 작업을 전달했을 때 번호가 붙은 두 섹션이 만들어지는지 검증합니다.
    report = combine_report("테스트 브리프", [("작업 A", "결과 A"), ("작업 B", "결과 B")])
    # 제목과 각 작업 섹션이 모두 포함되어야 합니다.
    assert "# 캠페인 실행안" in report and "## 1. 작업 A" in report and "## 2. 작업 B" in report

def test_yaml_contains_all_roles() -> None:
    # YAML에서 역할 프롬프트를 읽습니다.
    prompts = load_prompts()
    # 세 역할 키가 모두 존재하는지 검증합니다.
    assert {"planner", "worker", "reviewer"}.issubset(prompts)
