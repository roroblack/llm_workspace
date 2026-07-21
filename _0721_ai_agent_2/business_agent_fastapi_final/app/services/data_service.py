# -*- coding: utf-8 -*-
"""비즈니스 CSV 파일을 조회하고 요약하는 데이터 서비스입니다."""

# JSON 문자열 생성에 사용할 json 모듈을 가져옵니다.
import json
# 경로를 다루기 위해 Path 클래스를 가져옵니다.
from pathlib import Path
# 표 형식 데이터를 처리하기 위해 pandas를 가져옵니다.
import pandas as pd
# 공통 데이터 폴더 경로를 가져옵니다.
from app.core.settings import DATA_DIR


def list_data_files() -> list[dict[str, object]]:
    """data 폴더의 모든 파일을 상대경로와 크기로 반환합니다."""
    # 파일 목록을 담을 빈 리스트를 생성합니다.
    items: list[dict[str, object]] = []
    # data 폴더 아래의 모든 파일을 재귀적으로 순회합니다.
    for path in sorted(DATA_DIR.rglob("*")):
        # 폴더는 제외하고 실제 파일만 처리합니다.
        if path.is_file():
            # 프론트엔드와 API에서 사용하기 쉬운 딕셔너리 형태로 추가합니다.
            items.append({"path": str(path.relative_to(DATA_DIR)), "size_bytes": path.stat().st_size})
    # 완성된 파일 목록을 반환합니다.
    return items


def read_csv_preview(filename: str, limit: int = 10) -> dict[str, object]:
    """허용된 data 폴더 안의 CSV를 읽어 미리보기 정보를 반환합니다."""
    # 사용자가 전달한 파일명에서 디렉터리 탈출 문자열을 제거하기 위해 이름만 추출합니다.
    safe_name = Path(filename).name
    # data 폴더 내부의 최종 CSV 경로를 계산합니다.
    csv_path = DATA_DIR / safe_name
    # CSV 확장자가 아니거나 파일이 없으면 오류를 발생시킵니다.
    if csv_path.suffix.lower() != ".csv" or not csv_path.exists():
        raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {safe_name}")
    # 한글 BOM을 고려해 CSV를 데이터프레임으로 읽습니다.
    dataframe = pd.read_csv(csv_path, encoding="utf-8-sig")
    # API 응답 크기를 제한하기 위해 요청된 행 수만 선택합니다.
    preview = dataframe.head(max(1, min(limit, 100)))
    # 컬럼, 전체 행 수, 미리보기 레코드를 딕셔너리로 반환합니다.
    return {"filename": safe_name, "columns": list(dataframe.columns), "row_count": len(dataframe), "rows": preview.to_dict(orient="records")}


def summarize_business_data() -> str:
    """ReAct와 MCP 도구가 사용할 핵심 비즈니스 데이터 요약을 생성합니다."""
    # 핵심 파일명을 순서대로 정의합니다.
    targets = ["monthly_sales.csv", "competitor_data.csv", "products.csv", "inventory.csv", "orders.csv", "reviews.csv"]
    # 각 파일 요약을 담을 리스트를 생성합니다.
    summaries: list[str] = []
    # 핵심 파일을 하나씩 확인합니다.
    for filename in targets:
        # 대상 파일의 전체 경로를 계산합니다.
        path = DATA_DIR / filename
        # 파일이 없으면 해당 항목만 건너뜁니다.
        if not path.exists():
            continue
        # CSV를 데이터프레임으로 읽습니다.
        dataframe = pd.read_csv(path, encoding="utf-8-sig")
        # 파일명, 행 수, 컬럼명을 간결한 문자열로 추가합니다.
        summaries.append(f"- {filename}: {len(dataframe)}행 / 컬럼={list(dataframe.columns)}")
    # 줄바꿈으로 연결된 요약 문자열을 반환합니다.
    return "\n".join(summaries)
