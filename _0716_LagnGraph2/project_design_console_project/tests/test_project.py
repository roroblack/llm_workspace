# -*- coding: utf-8 -*-
"""외부 API를 호출하지 않고 프로젝트의 핵심 구조를 검증합니다."""

# 설계 클래스와 경로를 가져옵니다.
from app.project_design import AgentSpec
# 판단 함수와 입력 클래스를 가져옵니다.
from app.tradeoff import DesignSpec, decide
# 실습문제 문서 생성 함수를 가져옵니다.
from app.exercises import create_design_document
# 원본 공통 모듈의 데이터 경로를 가져옵니다.
from app.common_bridge import DATA


def test_data_exists() -> None:
    """앞서 제공된 data.zip의 핵심 파일이 프로젝트에 포함됐는지 검사합니다."""
    # 티켓 데이터가 존재해야 테스트가 통과합니다.
    assert (DATA / "support_tickets.csv").exists()
    # FAQ 데이터가 존재해야 테스트가 통과합니다.
    assert (DATA / "faq.csv").exists()


def test_default_design() -> None:
    """통합 CS 에이전트의 기본 설계 결정이 의도와 같은지 검사합니다."""
    # 기본 명세 객체를 생성합니다.
    spec = AgentSpec()
    # 정책 문서 때문에 RAG가 사용되어야 합니다.
    assert spec.use_rag is True
    # 도구 4개이므로 멀티에이전트는 보류되어야 합니다.
    assert spec.use_multi_agent is False


def test_tradeoff_rules() -> None:
    """역할이 3개인 시나리오에서 멀티에이전트가 추천되는지 검사합니다."""
    # 역할 세 개를 가진 설계 입력을 생성합니다.
    result = decide(DesignSpec(num_roles=3))
    # 멀티에이전트 도입 판단은 참이어야 합니다.
    assert result["멀티에이전트"]["도입"] is True


def test_exercise_document() -> None:
    """실습문제 설계 문서가 필수 섹션을 포함하는지 검사합니다."""
    # 문서를 생성하고 내용을 반환받습니다.
    text = create_design_document()
    # 요구사항 분석 섹션이 있어야 합니다.
    assert "## 1. 요구사항 분석" in text
    # 도구 목록 섹션이 있어야 합니다.
    assert "## 2. 도구 목록" in text
