# -*- coding: utf-8 -*-
"""data.zip에서 제공된 CSV/JSON 파일을 읽고 상담용 정보를 조회합니다."""

# csv 모듈은 CSV 파일을 표준 방식으로 읽기 위해 사용합니다.
import csv
# json 모듈은 JSON 형식의 사용자 프로필 파일을 읽기 위해 사용합니다.
import json
# dataclass는 고객 상담 컨텍스트를 명확한 구조로 표현하기 위해 사용합니다.
from dataclasses import dataclass
# Path는 운영체제와 무관한 파일 경로 처리를 위해 사용합니다.
from pathlib import Path

# 제공된 common.py의 DATA 경로 상수를 그대로 사용합니다.
from code.common import DATA


# dataclass는 조회한 고객 관련 정보를 하나의 객체로 묶습니다.
@dataclass
class CustomerContext:
    # 고객 기본 정보 행을 저장합니다.
    customer: dict[str, str] | None
    # 고객의 주문 목록을 저장합니다.
    orders: list[dict[str, str]]
    # 고객의 상담 문의 목록을 저장합니다.
    inquiries: list[dict[str, str]]
    # 고객의 장기 프로필 정보를 저장합니다.
    profile: dict | None


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    """UTF-8 CSV 파일을 딕셔너리 목록으로 읽습니다."""
    # 파일이 없으면 명확한 오류를 발생시켜 데이터 배치 문제를 알립니다.
    if not path.exists():
        raise FileNotFoundError(f"데이터 파일을 찾을 수 없습니다: {path}")
    # utf-8-sig는 일반 UTF-8과 BOM이 포함된 UTF-8을 모두 안전하게 처리합니다.
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        # DictReader는 첫 번째 행을 열 이름으로 사용합니다.
        reader = csv.DictReader(file)
        # 반복자를 리스트로 변환하여 호출 이후에도 데이터를 사용할 수 있게 합니다.
        return [dict(row) for row in reader]


def read_json(path: Path):
    """UTF-8 JSON 파일을 파이썬 객체로 읽습니다."""
    # 파일이 없으면 즉시 오류를 발생시킵니다.
    if not path.exists():
        raise FileNotFoundError(f"데이터 파일을 찾을 수 없습니다: {path}")
    # JSON 파일을 텍스트 읽기 모드로 엽니다.
    with path.open("r", encoding="utf-8-sig") as file:
        # json.load가 파일 내용을 파이썬 객체로 변환합니다.
        return json.load(file)


def _first_existing_key(row: dict, candidates: tuple[str, ...]) -> str | None:
    """후보 열 이름 중 실제 행에 존재하는 첫 번째 열 이름을 반환합니다."""
    # 후보 열 이름을 순서대로 검사합니다.
    for key in candidates:
        # 현재 열 이름이 행에 존재하면 그 이름을 반환합니다.
        if key in row:
            return key
    # 어느 후보도 없으면 None을 반환합니다.
    return None


def _match_id(row: dict, target_id: str) -> bool:
    """서로 다른 데이터 파일의 고객 식별자 열을 자동 탐색하여 비교합니다."""
    # 데이터 파일에서 자주 사용하는 고객 식별자 열 이름 후보를 정의합니다.
    key = _first_existing_key(row, ("customer_id", "customerId", "user_id", "id", "고객ID"))
    # 식별자 열이 없으면 해당 행은 일치하지 않는 것으로 처리합니다.
    if key is None:
        return False
    # 양쪽 값을 문자열로 바꾸고 공백을 제거한 뒤 비교합니다.
    return str(row.get(key, "")).strip() == target_id.strip()


def load_customer_context(customer_id: str) -> CustomerContext:
    """고객 ID로 고객, 주문, 상담 문의, 사용자 프로필을 통합 조회합니다."""
    # customers.csv의 모든 고객 행을 읽습니다.
    customers = read_csv_rows(DATA / "customers.csv")
    # orders.csv의 모든 주문 행을 읽습니다.
    orders = read_csv_rows(DATA / "orders.csv")
    # cs_inquiries.csv의 모든 상담 문의 행을 읽습니다.
    inquiries = read_csv_rows(DATA / "cs_inquiries.csv")
    # user_profiles.json의 프로필 데이터를 읽습니다.
    profiles = read_json(DATA / "user_profiles.json")

    # 입력한 고객 ID와 일치하는 첫 고객 행을 찾습니다.
    customer = next((row for row in customers if _match_id(row, customer_id)), None)
    # 입력한 고객 ID와 일치하는 주문만 필터링합니다.
    customer_orders = [row for row in orders if _match_id(row, customer_id)]
    # 입력한 고객 ID와 일치하는 상담 문의만 필터링합니다.
    customer_inquiries = [row for row in inquiries if _match_id(row, customer_id)]

    # JSON이 딕셔너리일 때 고객 ID를 키로 사용하는 구조를 먼저 확인합니다.
    profile = profiles.get(customer_id) if isinstance(profiles, dict) else None
    # JSON이 리스트이면 각 항목의 고객 ID를 검사합니다.
    if profile is None and isinstance(profiles, list):
        profile = next((row for row in profiles if isinstance(row, dict) and _match_id(row, customer_id)), None)

    # 통합 조회 결과를 CustomerContext 객체로 반환합니다.
    return CustomerContext(customer, customer_orders, customer_inquiries, profile)


def list_sample_customer_ids(limit: int = 10) -> list[str]:
    """실행 테스트에 사용할 고객 ID 예시를 반환합니다."""
    # 고객 데이터를 읽습니다.
    customers = read_csv_rows(DATA / "customers.csv")
    # 결과를 저장할 리스트를 만듭니다.
    result: list[str] = []
    # 고객 행을 순서대로 확인합니다.
    for row in customers:
        # 현재 파일에 실제로 존재하는 고객 ID 열을 찾습니다.
        key = _first_existing_key(row, ("customer_id", "customerId", "user_id", "id", "고객ID"))
        # 식별자 열이 존재하면 값을 문자열로 변환합니다.
        if key and str(row.get(key, "")).strip():
            result.append(str(row[key]).strip())
        # 지정한 개수만큼 수집했으면 반복을 종료합니다.
        if len(result) >= limit:
            break
    # 수집된 고객 ID 목록을 반환합니다.
    return result


def context_to_prompt(context: CustomerContext) -> str:
    """고객 통합 데이터를 LLM에 전달하기 좋은 텍스트로 변환합니다."""
    # 데이터 섹션을 저장할 리스트를 만듭니다.
    sections: list[str] = []
    # 고객 기본 정보를 문자열로 추가합니다.
    sections.append(f"[고객 기본 정보]\n{context.customer or '조회 결과 없음'}")
    # 최근 주문은 너무 길어지지 않도록 최대 5개만 추가합니다.
    sections.append(f"[최근 주문]\n{context.orders[:5] or '조회 결과 없음'}")
    # 최근 상담 문의도 최대 5개만 추가합니다.
    sections.append(f"[최근 상담 문의]\n{context.inquiries[:5] or '조회 결과 없음'}")
    # 사용자 프로필 정보를 추가합니다.
    sections.append(f"[사용자 프로필]\n{context.profile or '조회 결과 없음'}")
    # 각 섹션을 빈 줄로 구분하여 하나의 프롬프트로 반환합니다.
    return "\n\n".join(sections)
