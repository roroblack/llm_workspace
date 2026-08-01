# -*- coding: utf-8 -*-
"""제28강 실습문제 1과 2의 완성 코드입니다."""

# 데이터 파일을 읽기 위해 pandas를 가져옵니다.
import pandas as pd
# 설계 명세 객체를 만들기 위해 dataclass를 가져옵니다.
from dataclasses import dataclass
# 원본 common.py의 경로 상수를 가져옵니다.
from app.common_bridge import DATA, PROJECT_ROOT


# CS 티켓 에이전트 설계 명세를 데이터 객체로 정의합니다.
@dataclass
class TicketAgentSpec:
    """CS 티켓 자동 분류·답변 에이전트의 설계 결정입니다."""

    # 프로젝트 이름을 지정합니다.
    name: str = "CS 티켓 자동 분류·답변 에이전트"
    # 필요한 도구 이름을 지정합니다.
    tools: tuple[str, ...] = ("classify_severity", "search_faq", "draft_reply")
    # 짧은 FAQ CSV이므로 초기 버전에서는 RAG를 보류합니다.
    use_rag: bool = False
    # 티켓 단건 처리이므로 대화 메모리를 사용하지 않습니다.
    use_memory: bool = False
    # 도구가 3개이므로 단일 에이전트로 시작합니다.
    use_multi_agent: bool = False


def classify_severity(content: str) -> str:
    """티켓 본문을 긴급·보통·낮음으로 분류할 예정인 인터페이스입니다."""
    # 이번 실습은 설계 스켈레톤이므로 구현 예정 예외를 명확히 발생시킵니다.
    raise NotImplementedError("구현 예정")


def search_faq(keyword: str) -> str:
    """FAQ CSV에서 관련 답변을 찾을 예정인 인터페이스입니다."""
    # 이후 구현 단계에서 CSV 검색 코드로 대체할 예정임을 표시합니다.
    raise NotImplementedError("구현 예정")


def draft_reply(content: str, faq: str) -> str:
    """티켓과 FAQ 근거로 답변 초안을 작성할 예정인 인터페이스입니다."""
    # 이후 구현 단계에서 LLM 호출 코드로 대체할 예정임을 표시합니다.
    raise NotImplementedError("구현 예정")


def create_design_document() -> str:
    """실습문제 1의 설계 문서를 생성하고 docs 폴더에 저장합니다."""
    # 데이터 파일 존재와 컬럼을 실제로 확인하기 위해 티켓 CSV를 읽습니다.
    tickets = pd.read_csv(DATA / "support_tickets.csv")
    # FAQ 데이터 파일도 실제로 읽어 입력 자료가 준비됐는지 확인합니다.
    faq = pd.read_csv(DATA / "faq.csv")
    # 설계 문서의 완성된 마크다운 문자열을 작성합니다.
    document = f"""# CS 티켓 자동 분류·답변 에이전트 — 설계 문서

## 1. 요구사항 분석
- 입력: `data/support_tickets.csv`의 `content`
- 출력: severity(긴급/보통/낮음) + 답변 초안
- 확인된 티켓 수: {len(tickets)}건

## 2. 도구 목록
| 도구 | 입력 → 출력 | 설명 |
|---|---|---|
| classify_severity | str → str | 심각도 분류 |
| search_faq | str → str | FAQ 검색 |
| draft_reply | (str, str) → str | 답변 초안 생성 |

## 3. 데이터 흐름
티켓 입력 → 심각도 분류 → FAQ 검색 → 답변 초안 → 최종 결과

## 4. 텍스트 아키텍처
support_tickets.csv → classify_severity → search_faq({len(faq)}건) → draft_reply → 출력

## 5. 구성요소 판단
- RAG: 보류 — 현재 FAQ는 CSV 검색으로 충분
- 메모리: 제외 — 티켓 단건 처리
- 멀티에이전트: 제외 — 도구 3개
"""
    # 설계 문서를 저장할 docs 폴더를 지정합니다.
    docs_dir = PROJECT_ROOT / "docs"
    # docs 폴더가 없으면 자동으로 생성합니다.
    docs_dir.mkdir(parents=True, exist_ok=True)
    # 최종 문서 파일 경로를 구성합니다.
    output_path = docs_dir / "cs_agent_design.md"
    # 한글이 깨지지 않도록 UTF-8로 문서를 저장합니다.
    output_path.write_text(document, encoding="utf-8")
    # 저장 결과를 사용자에게 출력합니다.
    print(f"설계 문서 저장 완료: {output_path}")
    # 생성한 문서 내용을 호출자에게 반환합니다.
    return document


def print_exercise_skeleton() -> None:
    """실습문제 2의 코드 스켈레톤 설계 내용을 출력합니다."""
    # 기본 티켓 에이전트 명세 객체를 생성합니다.
    spec = TicketAgentSpec()
    # 설계 제목을 출력합니다.
    print(f"[실습문제 2] {spec.name}")
    # 도구 목록을 출력합니다.
    print(f"도구: {', '.join(spec.tools)}")
    # 데이터 흐름을 출력합니다.
    print("흐름: content → classify_severity → search_faq → draft_reply")
    # 과잉 구성요소를 제외한 판단 결과를 출력합니다.
    print(f"RAG={spec.use_rag}, 메모리={spec.use_memory}, 멀티에이전트={spec.use_multi_agent}")
