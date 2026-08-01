# -*- coding: utf-8 -*-
"""data.zip의 CSV 데이터를 근거로 검색 없이 리포트를 생성하는 모듈입니다."""

# 안전한 파일 경로 처리를 위해 pathlib을 가져옵니다.
import pathlib

# 표 데이터 처리를 위해 pandas를 사용합니다.
import pandas as pd

# 제공된 공통 모듈에서 데이터 경로와 LLM 생성 함수를 가져옵니다.
from common import DATA, get_chat
# 현재 선택한 모델 공급자를 가져옵니다.
from app_context import get_provider
# 모델 응답을 문자열로 통일합니다.
from message_utils import extract_text
# 마크다운 저장 기능을 재사용합니다.
from research_service import REPORTS, save_report


def dataframe_to_prompt_table(dataframe: pd.DataFrame) -> str:
    """DataFrame을 LLM 프롬프트에 넣기 좋은 표 문자열로 변환합니다."""
    try:
        # tabulate가 설치되어 있으면 읽기 좋은 마크다운 표를 생성합니다.
        return dataframe.to_markdown(index=False)
    except ImportError:
        # tabulate가 없더라도 앱이 멈추지 않도록 일반 고정폭 표로 대체합니다.
        return dataframe.to_string(index=False)


def make_competitor_report() -> tuple[str, pathlib.Path, list[str]]:
    """competitor_data.csv를 근거로 모든 경쟁사를 포함한 분석 리포트를 생성합니다."""
    # data.zip에서 추출한 경쟁사 CSV 경로를 지정합니다.
    csv_path = DATA / "competitor_data.csv"

    # Excel에서 저장한 BOM이 있어도 읽을 수 있도록 utf-8-sig 인코딩을 사용합니다.
    dataframe = pd.read_csv(csv_path, encoding="utf-8-sig")

    # 검증에 사용할 실제 경쟁사 이름 목록을 문자열로 변환합니다.
    companies = dataframe["company"].astype(str).tolist()

    # LLM이 표 구조를 이해하기 쉽게 마크다운 또는 고정폭 표로 변환합니다.
    table = dataframe_to_prompt_table(dataframe)

    # 사실 기반 분석이면서 자연스러운 서술을 위해 temperature 0.3으로 모델을 생성합니다.
    llm = get_chat(provider=get_provider(), temperature=0.3)

    # 표 밖의 사실을 지어내지 않고 모든 경쟁사를 언급하도록 강하게 지시합니다.
    prompt = (
        "너는 승승장구몰의 시장 조사 애널리스트다. 아래 경쟁사 CSV 표만을 근거로 분석하라. "
        "표에 없는 최신 시장 수치나 사실은 만들지 마라. "
        "한국어 마크다운으로 작성하고 '## 개요', '## 경쟁사별 강약점', '## 비교 요약', "
        "'## 시사점' 섹션을 정확히 포함하라. "
        "표에 있는 모든 경쟁사 이름을 빠짐없이 한 번 이상 언급하라.\n\n"
        f"{table}"
    )

    # 모델이 작성한 분석 본문을 문자열로 변환합니다.
    body = extract_text(llm.invoke(prompt))

    # 실습문제 요구 파일명 competitor_report.md로 저장하기 위해 reports 폴더를 준비합니다.
    REPORTS.mkdir(parents=True, exist_ok=True)

    # 요구된 고정 파일 경로를 만듭니다.
    path = REPORTS / "competitor_report.md"

    # 제목과 본문을 UTF-8로 저장합니다.
    path.write_text("# 경쟁사 분석 리포트\n\n" + body.strip() + "\n", encoding="utf-8")

    # 본문에서 누락된 회사가 있는지 확인해 경고 문구를 추가합니다.
    missing = [company for company in companies if company not in body]

    # 누락 목록이 있으면 사용자가 검증 실패를 바로 알 수 있게 콘솔에 출력합니다.
    if missing:
        print(f"[검증 경고] 리포트에서 누락된 경쟁사: {', '.join(missing)}")
    else:
        print(f"[검증 성공] {len(companies)}개 경쟁사 이름이 모두 포함되었습니다.")

    # 본문, 저장 경로, 경쟁사 목록을 반환합니다.
    return body, path, companies


def make_internal_sales_report() -> tuple[str, pathlib.Path]:
    """monthly_sales.csv와 products.csv를 결합해 내부 데이터 기반 리포트를 생성합니다."""
    # 월별 매출 데이터를 읽습니다.
    monthly_sales = pd.read_csv(DATA / "monthly_sales.csv", encoding="utf-8-sig")

    # 상품 기준 정보를 읽습니다.
    products = pd.read_csv(DATA / "products.csv", encoding="utf-8-sig")

    # 원본 데이터가 매우 크지 않더라도 프롬프트 길이를 통제하기 위해 요약 정보를 만듭니다.
    sales_preview = monthly_sales.head(30)

    # 상품 데이터도 앞부분 최대 30행만 표로 사용합니다.
    products_preview = products.head(30)

    # 두 DataFrame을 읽기 가능한 표 문자열로 변환합니다.
    sales_table = dataframe_to_prompt_table(sales_preview)
    products_table = dataframe_to_prompt_table(products_preview)

    # 내부 데이터 분석용 LLM을 생성합니다.
    llm = get_chat(provider=get_provider(), temperature=0.2)

    # 데이터에 없는 외부 최신 사실을 섞지 않도록 출처 범위를 명확히 제한합니다.
    prompt = (
        "너는 사내 데이터 분석가다. 아래 monthly_sales.csv와 products.csv 발췌 데이터만 근거로 "
        "판매 동향과 상품 운영 시사점을 분석하라. 데이터에 없는 수치는 만들지 마라. "
        "'## 데이터 개요', '## 판매 동향', '## 상품 관점 분석', '## 실행 제안', '## 분석 한계' "
        "섹션을 포함한 한국어 마크다운 리포트를 작성하라.\n\n"
        f"[monthly_sales.csv 발췌]\n{sales_table}\n\n"
        f"[products.csv 발췌]\n{products_table}"
    )

    # 분석 결과를 문자열로 추출합니다.
    body = extract_text(llm.invoke(prompt))

    # 공통 저장 함수를 사용해 날짜와 모델 공급자 헤더를 포함한 파일을 만듭니다.
    path = save_report("내부 판매 및 상품 데이터 분석", body, prefix="internal_data")

    # 본문과 저장 경로를 반환합니다.
    return body, path
