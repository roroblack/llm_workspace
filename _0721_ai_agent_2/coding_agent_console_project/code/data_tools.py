# -*- coding: utf-8 -*-
"""data.zip의 데이터 파일 상태와 예제 실행 결과를 확인하는 보조 모듈입니다."""

import csv
from pathlib import Path

from common import DATA


def list_data_files() -> list[Path]:
    """data 폴더 안의 모든 파일을 상대경로 기준으로 정렬해 반환합니다."""
    return sorted(path for path in DATA.rglob("*") if path.is_file())


def inspect_sales_csv(limit: int = 5) -> list[dict[str, str]]:
    """코딩 에이전트가 처리할 sales_daily.csv의 앞부분을 읽어 반환합니다."""
    csv_path = DATA / "sales_daily.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"필수 데이터가 없습니다: {csv_path}")
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        rows: list[dict[str, str]] = []
        for index, row in enumerate(reader):
            if index >= limit:
                break
            rows.append(dict(row))
    return rows
