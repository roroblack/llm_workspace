# -*- coding: utf-8 -*-
"""제24강 비즈니스 리포트 에이전트의 집계·서술·저장 파이프라인입니다."""

import datetime
from pathlib import Path
from typing import Optional
import pandas as pd
from app.core.common import DATA, ROOT, get_chat
from app.services.provider_context import get_provider
from app.services.message_utils import extract_text

# 보고서 저장 위치를 프로젝트 루트 아래 reports 폴더로 고정합니다.
REPORTS_DIR = ROOT / "reports"
# 기본 분석 파일을 data.zip에서 제공된 monthly_sales.csv로 지정합니다.
DEFAULT_SALES_PATH = DATA / "monthly_sales.csv"
# 집계에 반드시 필요한 컬럼을 상수로 관리합니다.
REQUIRED_COLUMNS = {"month", "total"}


def _read_sales_dataframe(csv_path: Path = DEFAULT_SALES_PATH) -> pd.DataFrame:
    """월간 매출 CSV를 읽고 기본 유효성을 검사한 DataFrame을 반환합니다."""
    # 파일 존재 여부를 pandas 호출 전에 검사해 더 친절한 오류를 제공합니다.
    if not csv_path.exists():
        raise FileNotFoundError(f"매출 파일을 찾지 못했습니다: {csv_path}")
    # BOM이 포함된 한글 CSV도 정상 처리하도록 utf-8-sig 인코딩을 사용합니다.
    dataframe = pd.read_csv(csv_path, encoding="utf-8-sig")
    # 행이 하나도 없으면 최신 달과 전월을 선택할 수 없으므로 중단합니다.
    if dataframe.empty:
        raise ValueError("매출 데이터가 비어 있습니다.")
    # 필수 컬럼 중 현재 CSV에 없는 컬럼을 계산합니다.
    missing = sorted(REQUIRED_COLUMNS - set(dataframe.columns))
    # 누락 컬럼이 있으면 현재 컬럼 정보까지 포함해 원인을 명확히 알립니다.
    if missing:
        raise ValueError(f"필수 컬럼이 누락되었습니다: {missing} / 현재 컬럼: {list(dataframe.columns)}")
    # month 문자열을 기준으로 오름차순 정렬한 뒤 인덱스를 다시 부여합니다.
    dataframe = dataframe.sort_values("month").reset_index(drop=True)
    # total과 카테고리 숫자 컬럼을 숫자로 변환하고 실패 값은 NaN으로 둡니다.
    numeric_columns = [column for column in dataframe.columns if column != "month"]
    # 각 숫자 컬럼에 안전한 숫자 변환을 적용합니다.
    for column in numeric_columns:
        dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")
    # 숫자 변환 실패나 데이터 누락이 하나라도 있으면 잘못된 계산을 막습니다.
    if dataframe[numeric_columns].isna().any().any():
        bad_columns = dataframe[numeric_columns].columns[dataframe[numeric_columns].isna().any()].tolist()
        raise ValueError(f"숫자 변환 실패 또는 누락값이 있습니다: {bad_columns}")
    # 검증을 통과한 데이터프레임을 반환합니다.
    return dataframe


def _build_facts(dataframe: pd.DataFrame, row_index: int) -> dict:
    """지정된 행과 바로 이전 행을 비교해 확정 수치 facts를 생성합니다."""
    # 첫 번째 행은 이전 달이 없어 증감률을 계산할 수 없습니다.
    if row_index <= 0:
        raise ValueError("첫 번째 달은 전월 데이터가 없어 증감률을 계산할 수 없습니다.")
    # 범위를 벗어난 인덱스는 명확한 오류로 처리합니다.
    if row_index >= len(dataframe):
        raise IndexError("분석할 행 인덱스가 데이터 범위를 벗어났습니다.")
    # 현재 달과 이전 달 행을 각각 선택합니다.
    current = dataframe.iloc[row_index]
    previous = dataframe.iloc[row_index - 1]
    # month와 total을 제외한 나머지 컬럼을 카테고리 매출로 간주합니다.
    category_columns = [column for column in dataframe.columns if column not in {"month", "total"}]
    # 카테고리가 두 개 미만이면 1위와 2위를 계산할 수 없습니다.
    if len(category_columns) < 2:
        raise ValueError("카테고리 매출 컬럼이 최소 2개 필요합니다.")
    # 현재 달 카테고리 매출을 큰 값부터 내림차순으로 정렬합니다.
    current_categories = current[category_columns].sort_values(ascending=False)
    # 이전 달 총매출이 0이면 증감률 나눗셈이 불가능합니다.
    if float(previous["total"]) == 0:
        raise ZeroDivisionError("전월 총매출이 0이라 증감률을 계산할 수 없습니다.")
    # 증감률은 코드가 정확히 계산하도록 합니다.
    growth = (float(current["total"]) - float(previous["total"])) / float(previous["total"]) * 100
    # LLM이 사용할 수치와 설명용 정보를 하나의 딕셔너리로 확정합니다.
    return {
        "month": str(current["month"]),
        "prev_month": str(previous["month"]),
        "total": int(current["total"]),
        "prev_total": int(previous["total"]),
        "growth_pct": round(growth, 1),
        "top_category": str(current_categories.index[0]),
        "top_value": int(current_categories.iloc[0]),
        "second_category": str(current_categories.index[1]),
        "second_value": int(current_categories.iloc[1]),
        "by_category": {str(key): int(value) for key, value in current_categories.items()},
    }


def load_facts(csv_path: Path = DEFAULT_SALES_PATH) -> dict:
    """CSV의 최신 달과 전월을 비교한 facts를 반환합니다."""
    # 공통 CSV 읽기와 검증 함수를 호출합니다.
    dataframe = _read_sales_dataframe(csv_path)
    # 최신 달은 정렬된 데이터프레임의 마지막 행이므로 len-1을 전달합니다.
    return _build_facts(dataframe, len(dataframe) - 1)


def load_facts_for_month(month: str, csv_path: Path = DEFAULT_SALES_PATH) -> dict:
    """사용자가 지정한 달과 전월을 비교한 facts를 반환합니다."""
    # 입력된 월의 앞뒤 공백을 제거합니다.
    target_month = month.strip()
    # 월간 매출 데이터를 안전하게 읽습니다.
    dataframe = _read_sales_dataframe(csv_path)
    # 비교를 안정적으로 하기 위해 month 컬럼을 문자열로 변환합니다.
    month_values = dataframe["month"].astype(str)
    # 존재하지 않는 달이면 선택 가능한 달 목록을 함께 안내합니다.
    if target_month not in set(month_values):
        available = ", ".join(month_values.tolist())
        raise ValueError(f"'{target_month}' 데이터가 없습니다. 사용 가능한 달: {available}")
    # 지정 달이 위치한 첫 번째 인덱스를 가져옵니다.
    row_index = int(dataframe.index[month_values == target_month][0])
    # 공통 facts 생성 함수를 사용해 중복 계산 코드를 제거합니다.
    return _build_facts(dataframe, row_index)


def _failure_facts(message: str) -> dict:
    """안전 집계 실패 시에도 동일한 키 구조를 유지하는 기본값을 반환합니다."""
    # 호출부가 KeyError 없이 공통 키를 읽을 수 있도록 성공 facts와 같은 구조를 제공합니다.
    return {
        "ok": False,
        "error": message,
        "month": "N/A",
        "prev_month": "N/A",
        "total": 0,
        "prev_total": 0,
        "growth_pct": 0.0,
        "top_category": "없음",
        "top_value": 0,
        "second_category": "없음",
        "second_value": 0,
        "by_category": {},
    }


def load_facts_safe(csv_path: Path = DEFAULT_SALES_PATH) -> dict:
    """모든 오류를 사람이 읽을 메시지로 바꾸고 항상 dict를 반환합니다."""
    try:
        # 일반 집계 함수를 그대로 재사용해 계산 로직의 단일 출처를 유지합니다.
        facts = load_facts(csv_path)
        # 성공 여부를 호출부가 쉽게 판단하도록 ok 키를 추가합니다.
        return {"ok": True, "error": "", **facts}
    except Exception as error:
        # 예외 유형과 메시지를 함께 담아 진단 가능한 실패 결과를 만듭니다.
        return _failure_facts(f"{type(error).__name__}: {error}")


def format_facts(facts: dict) -> str:
    """확정 수치를 콘솔과 프롬프트에서 재사용할 문자열로 변환합니다."""
    # 카테고리별 매출을 마크다운 목록 형식으로 만듭니다.
    category_lines = "\n".join(f"- {name}: {value:,}원" for name, value in facts["by_category"].items())
    # LLM이 계산하지 않도록 모든 숫자를 사람이 읽는 형태로 미리 제공합니다.
    return (
        f"- 대상 월: {facts['month']}\n"
        f"- 전월: {facts['prev_month']}\n"
        f"- 총매출: {facts['total']:,}원\n"
        f"- 전월 총매출: {facts['prev_total']:,}원\n"
        f"- 전월 대비 증감률: {facts['growth_pct']:+.1f}%\n"
        f"- 최대 카테고리: {facts['top_category']} {facts['top_value']:,}원\n"
        f"- 2위 카테고리: {facts['second_category']} {facts['second_value']:,}원\n"
        f"[카테고리별 매출]\n{category_lines}"
    )


def write_report(facts: dict) -> str:
    """확정 facts만 근거로 OpenAI 또는 Gemini가 한국어 보고서를 작성합니다."""
    # 현재 사용자가 선택한 공급자와 temperature 0.3으로 LangChain 모델을 생성합니다.
    llm = get_chat(provider=get_provider(), temperature=0.3)
    # 숫자는 새로 계산하거나 만들지 못하게 하고 보고서 구조를 명확히 제한합니다.
    prompt = (
        "너는 온라인 쇼핑몰 경영기획 담당자다. 아래 [확정 수치]만 근거로 "
        "경영진용 한국어 월간 매출 보고서를 마크다운으로 작성하라. "
        "주어진 숫자를 변경하거나 새로운 수치를 계산·추측·창작하지 마라. "
        "원인에 대한 단정 대신 데이터에서 관찰되는 추세라고 표현하라. "
        "반드시 '## 총평', '## 카테고리 분석', '## 다음 달 제언' 세 섹션을 포함하라.\n\n"
        f"[확정 수치]\n{format_facts(facts)}"
    )
    # 모델에 프롬프트를 전달하고 응답 객체를 받습니다.
    response = llm.invoke(prompt)
    # 공급자별 응답 형식 차이를 공통 문자열로 변환합니다.
    return extract_text(response)


def make_fallback_report(facts: dict, reason: str = "") -> str:
    """API 호출이 불가능할 때도 확정 수치만으로 기본 보고서를 생성합니다."""
    # 증감률 부호에 따라 추세 표현을 선택합니다.
    trend = "증가" if facts["growth_pct"] > 0 else "감소" if facts["growth_pct"] < 0 else "보합"
    # LLM 없이도 숫자를 바꾸지 않는 재현 가능한 보고서를 작성합니다.
    body = (
        "## 총평\n"
        f"{facts['month']} 총매출은 {facts['total']:,}원이며, "
        f"{facts['prev_month']}의 {facts['prev_total']:,}원과 비교해 "
        f"{abs(facts['growth_pct']):.1f}% {trend}했습니다.\n\n"
        "## 카테고리 분석\n"
        f"가장 큰 매출 카테고리는 {facts['top_category']}({facts['top_value']:,}원)이며, "
        f"2위는 {facts['second_category']}({facts['second_value']:,}원)입니다.\n\n"
        "## 다음 달 제언\n"
        "상위 카테고리의 판매 요인을 유지하면서 하위 카테고리의 상품 구성과 프로모션 반응을 추가 점검합니다."
    )
    # 실패 이유가 있으면 문서 하단에 자동 대체 보고서임을 표시합니다.
    if reason:
        body += f"\n\n> LLM 호출 실패로 기본 템플릿을 사용했습니다: {reason}"
    # 완성된 기본 보고서를 반환합니다.
    return body


def write_report_with_fallback(facts: dict) -> str:
    """LLM 보고서 생성을 시도하고 실패하면 코드 기반 보고서로 대체합니다."""
    try:
        # 우선 선택한 OpenAI 또는 Gemini 모델로 자연어 보고서를 만듭니다.
        return write_report(facts)
    except Exception as error:
        # API 키, 네트워크, 할당량 문제로 실패해도 앱이 종료되지 않도록 폴백합니다.
        return make_fallback_report(facts, f"{type(error).__name__}: {error}")


def save_report(facts: dict, body: str, filename: Optional[str] = None) -> Path:
    """보고서를 UTF-8 마크다운 파일로 저장하고 경로를 반환합니다."""
    # reports 폴더가 없을 때 자동으로 생성합니다.
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    # 별도 파일명이 없으면 월별 표준 이름을 사용합니다.
    report_name = filename or f"monthly_sales_{facts['month']}.md"
    # 저장 대상 전체 경로를 구성합니다.
    report_path = REPORTS_DIR / report_name
    # 문서 제목과 자동 생성일을 헤더에 기록합니다.
    header = (
        f"# {facts['month']} 월간 매출 보고서\n\n"
        f"> 생성일: {datetime.date.today().isoformat()} / 자동 생성\n\n"
    )
    # 한글이 보존되도록 UTF-8로 전체 문서를 저장합니다.
    report_path.write_text(header + body.strip() + "\n", encoding="utf-8")
    # 호출부가 저장 결과를 출력하거나 후속 처리할 수 있도록 경로를 반환합니다.
    return report_path


def generate_monthly_report(month: Optional[str] = None) -> Path:
    """집계→LLM 서술→마크다운 저장을 한 번에 실행합니다."""
    # month가 주어졌으면 특정 달, 없으면 최신 달 facts를 계산합니다.
    facts = load_facts_for_month(month) if month else load_facts()
    # API 장애까지 고려한 안전한 보고서 생성 함수를 사용합니다.
    body = write_report_with_fallback(facts)
    # 완성된 보고서를 저장하고 저장 경로를 반환합니다.
    return save_report(facts, body)
