# -*- coding: utf-8 -*-
"""JSON과 SQLite를 사용하는 장기 기억 저장소 및 LangChain 도구 모듈입니다."""

# json 모듈은 파이썬 딕셔너리와 JSON 파일 사이를 변환하기 위해 사용합니다.
import json
# shutil 모듈은 원본 JSON 파일을 읽기·쓰기용 복사본으로 복사하기 위해 사용합니다.
import shutil
# sqlite3 모듈은 별도 서버 없이 파일 기반 SQLite 데이터베이스를 사용하기 위해 가져옵니다.
import sqlite3
# RLock은 여러 함수가 저장소에 접근할 때 파일 읽기·쓰기를 안전하게 직렬화합니다.
from threading import RLock
# Any는 프로필 값이 문자열, 목록 등 여러 형식일 수 있음을 타입으로 표현합니다.
from typing import Any

# tool 데코레이터는 일반 파이썬 함수를 LLM 에이전트가 호출할 수 있는 도구로 변환합니다.
from langchain_core.tools import tool

# 제공된 common.py의 DATA 상수를 사용하여 data.zip에서 추출된 데이터 경로를 찾습니다.
from code.common import DATA

# 원본 프로필 파일 경로를 지정하며, 이 파일은 실습 중 직접 수정하지 않습니다.
JSON_SOURCE = DATA / "user_profiles.json"
# 읽기·쓰기 실습에 사용할 복사본 파일 경로를 지정합니다.
JSON_STORE = DATA / "user_profiles_rw.json"
# SQLite 장기 기억 데이터베이스 파일 경로를 지정합니다.
SQLITE_DB = DATA / "profiles.db"
# JSON 저장소를 동시에 수정할 때 충돌을 줄이기 위한 재진입 잠금을 생성합니다.
_JSON_LOCK = RLock()
# 사용자가 변경할 수 있는 프로필 필드만 화이트리스트로 정의합니다.
ALLOWED_FIELDS = {"name", "선호카테고리", "membership", "관심사", "비고"}


def ensure_json_store() -> None:
    """읽기·쓰기용 JSON 복사본이 없으면 원본에서 안전하게 생성합니다."""
    # 원본 파일이 없으면 data.zip 배치가 잘못된 것이므로 명확한 오류를 발생시킵니다.
    if not JSON_SOURCE.exists():
        # 누락된 실제 경로를 포함하여 문제 해결이 쉽도록 FileNotFoundError를 발생시킵니다.
        raise FileNotFoundError(f"원본 프로필 파일이 없습니다: {JSON_SOURCE}")
    # 읽기·쓰기용 파일이 아직 없는 최초 실행인지 확인합니다.
    if not JSON_STORE.exists():
        # 원본 보존을 위해 원본을 복사본 경로로 복사합니다.
        shutil.copy2(JSON_SOURCE, JSON_STORE)


def load_json_profiles() -> dict[str, dict[str, Any]]:
    """읽기·쓰기용 JSON 프로필 전체를 딕셔너리로 읽어 반환합니다."""
    # 한 스레드가 파일을 읽는 동안 다른 스레드가 쓰지 못하도록 잠금을 획득합니다.
    with _JSON_LOCK:
        # 복사본 파일이 없으면 원본을 바탕으로 자동 생성합니다.
        ensure_json_store()
        # 한글 데이터가 깨지지 않도록 UTF-8 인코딩으로 파일을 엽니다.
        with JSON_STORE.open("r", encoding="utf-8") as file:
            # JSON 문서를 파이썬 딕셔너리로 변환하여 반환합니다.
            return json.load(file)


def save_json_profiles(data: dict[str, dict[str, Any]]) -> None:
    """프로필 딕셔너리를 읽기·쓰기용 JSON 파일에 영속 저장합니다."""
    # 파일 저장 중 다른 읽기·쓰기가 끼어들지 않도록 잠금을 획득합니다.
    with _JSON_LOCK:
        # 저장 중 중단되어 원본 파일이 손상되는 위험을 줄이기 위한 임시 파일 경로를 만듭니다.
        temporary_path = JSON_STORE.with_suffix(".json.tmp")
        # 임시 파일을 UTF-8 쓰기 모드로 엽니다.
        with temporary_path.open("w", encoding="utf-8") as file:
            # 한글을 그대로 보존하고 들여쓰기를 적용하여 사람이 읽기 쉬운 JSON으로 저장합니다.
            json.dump(data, file, ensure_ascii=False, indent=2)
        # 저장이 끝난 임시 파일을 실제 저장소 파일로 원자적으로 교체합니다.
        temporary_path.replace(JSON_STORE)


def read_json_profile(customer_id: str) -> dict[str, Any] | None:
    """JSON 저장소에서 고객 ID에 해당하는 프로필을 조회합니다."""
    # 전체 JSON 프로필을 읽습니다.
    profiles = load_json_profiles()
    # 요청한 고객 ID가 있으면 프로필을, 없으면 None을 반환합니다.
    return profiles.get(customer_id)


def write_json_profile(customer_id: str, field: str, value: str) -> str:
    """JSON 저장소에서 특정 고객의 한 필드를 갱신합니다."""
    # 허용되지 않은 필드는 저장하지 않아 임의 데이터 구조 변경을 방지합니다.
    if field not in ALLOWED_FIELDS:
        # 사용 가능한 필드 목록과 함께 오류 메시지를 반환합니다.
        return f"'{field}'은(는) 갱신할 수 없습니다. 허용 필드: {', '.join(sorted(ALLOWED_FIELDS))}"
    # JSON 저장소 전체를 읽습니다.
    profiles = load_json_profiles()
    # 신규 고객이면 기본 프로필 구조를 생성하고, 기존 고객이면 해당 프로필을 가져옵니다.
    profile = profiles.setdefault(
        customer_id,
        {"name": "", "선호카테고리": [], "membership": "", "관심사": "", "비고": ""},
    )
    # 선호카테고리는 쉼표로 입력한 문자열을 목록으로 정규화합니다.
    if field == "선호카테고리":
        # 쉼표로 분리한 뒤 양쪽 공백을 제거하고 빈 값은 제외합니다.
        profile[field] = [item.strip() for item in value.split(",") if item.strip()]
    # 선호카테고리 이외 필드는 문자열 그대로 저장합니다.
    else:
        # 지정한 프로필 필드 값을 새 값으로 교체합니다.
        profile[field] = value
    # 변경된 전체 프로필을 JSON 파일에 영속 저장합니다.
    save_json_profiles(profiles)
    # 호출 결과를 사용자가 이해할 수 있는 문자열로 반환합니다.
    return f"{customer_id}의 '{field}'을(를) '{value}'(으)로 저장했습니다."


def reset_json_store() -> None:
    """읽기·쓰기용 JSON 저장소를 data.zip의 원본 상태로 되돌립니다."""
    # 원본 파일의 존재 여부를 먼저 확인합니다.
    if not JSON_SOURCE.exists():
        # 원본이 없으면 복구할 수 없으므로 오류를 발생시킵니다.
        raise FileNotFoundError(f"원본 프로필 파일이 없습니다: {JSON_SOURCE}")
    # 파일 복사를 동기화하기 위해 잠금을 획득합니다.
    with _JSON_LOCK:
        # 원본 파일을 읽기·쓰기용 저장소에 덮어써서 초기 상태로 복구합니다.
        shutil.copy2(JSON_SOURCE, JSON_STORE)


def init_sqlite_from_json(force_reset: bool = False) -> None:
    """SQLite 테이블을 만들고 필요한 경우 JSON 원본 데이터를 이관합니다."""
    # 강제 초기화를 선택했고 기존 DB가 있으면 삭제하여 완전히 새로 만듭니다.
    if force_reset and SQLITE_DB.exists():
        # 기존 데이터베이스 파일을 삭제합니다.
        SQLITE_DB.unlink()
    # SQLite 파일에 연결하며 with 블록 종료 시 변경 사항이 자동 커밋됩니다.
    with sqlite3.connect(SQLITE_DB) as connection:
        # 고객별 한 행을 저장하는 profiles 테이블이 없으면 생성합니다.
        connection.execute(
            "CREATE TABLE IF NOT EXISTS profiles ("
            "customer_id TEXT PRIMARY KEY, "
            "name TEXT NOT NULL DEFAULT '', "
            "membership TEXT NOT NULL DEFAULT '', "
            "선호카테고리 TEXT NOT NULL DEFAULT '[]', "
            "관심사 TEXT NOT NULL DEFAULT '', "
            "비고 TEXT NOT NULL DEFAULT ''"
            ")"
        )
        # 현재 테이블에 저장된 행 수를 조회합니다.
        row_count = connection.execute("SELECT COUNT(*) FROM profiles").fetchone()[0]
        # 테이블이 비어 있을 때만 JSON 데이터를 최초 한 번 이관합니다.
        if row_count == 0:
            # data.zip에서 제공된 원본 프로필 데이터를 읽습니다.
            profiles = json.loads(JSON_SOURCE.read_text(encoding="utf-8"))
            # 고객별 프로필을 순회하며 SQLite 행으로 변환합니다.
            for customer_id, profile in profiles.items():
                # SQL 값은 모두 ? 자리표시자로 바인딩하여 인젝션과 따옴표 오류를 방지합니다.
                connection.execute(
                    "INSERT INTO profiles "
                    "(customer_id, name, membership, 선호카테고리, 관심사, 비고) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        customer_id,
                        profile.get("name", ""),
                        profile.get("membership", ""),
                        json.dumps(profile.get("선호카테고리", []), ensure_ascii=False),
                        profile.get("관심사", ""),
                        profile.get("비고", ""),
                    ),
                )


def read_sqlite_profile(customer_id: str) -> dict[str, Any] | None:
    """SQLite에서 고객 한 행만 조회하여 프로필 딕셔너리로 반환합니다."""
    # DB와 테이블이 준비되어 있는지 확인하고 없으면 자동 초기화합니다.
    init_sqlite_from_json()
    # SQLite 데이터베이스에 연결합니다.
    with sqlite3.connect(SQLITE_DB) as connection:
        # 조회 결과를 컬럼명으로 접근할 수 있도록 Row 팩토리를 설정합니다.
        connection.row_factory = sqlite3.Row
        # 고객 ID는 ? 파라미터로 안전하게 바인딩하여 한 행만 조회합니다.
        row = connection.execute(
            "SELECT customer_id, name, membership, 선호카테고리, 관심사, 비고 "
            "FROM profiles WHERE customer_id = ?",
            (customer_id,),
        ).fetchone()
    # 조회 결과가 없으면 None을 반환합니다.
    if row is None:
        # 존재하지 않는 고객임을 호출자에게 알립니다.
        return None
    # sqlite3.Row를 일반 딕셔너리로 변환합니다.
    profile = dict(row)
    # DB에 JSON 문자열로 저장한 선호카테고리를 다시 파이썬 목록으로 변환합니다.
    profile["선호카테고리"] = json.loads(profile.get("선호카테고리") or "[]")
    # 변환한 프로필을 반환합니다.
    return profile


def write_sqlite_profile(customer_id: str, field: str, value: str) -> str:
    """SQLite에서 허용된 프로필 필드 하나를 안전하게 갱신합니다."""
    # 컬럼명은 SQL 파라미터로 바인딩할 수 없으므로 화이트리스트로 엄격히 제한합니다.
    if field not in ALLOWED_FIELDS:
        # 허용되지 않은 필드는 즉시 거부합니다.
        return f"'{field}'은(는) 갱신할 수 없습니다. 허용 필드: {', '.join(sorted(ALLOWED_FIELDS))}"
    # DB와 테이블을 준비하고 최초 데이터 이관을 수행합니다.
    init_sqlite_from_json()
    # 선호카테고리는 JSON 배열 문자열로 변환하여 저장합니다.
    normalized_value = (
        json.dumps([item.strip() for item in value.split(",") if item.strip()], ensure_ascii=False)
        if field == "선호카테고리"
        else value
    )
    # SQLite 데이터베이스에 연결합니다.
    with sqlite3.connect(SQLITE_DB) as connection:
        # 고객이 없을 때도 갱신할 수 있도록 기본 행을 먼저 생성하며 중복이면 무시합니다.
        connection.execute("INSERT OR IGNORE INTO profiles (customer_id) VALUES (?)", (customer_id,))
        # 컬럼명은 검증된 화이트리스트 값만 사용하고, 실제 값과 고객 ID는 ?로 바인딩합니다.
        connection.execute(
            f"UPDATE profiles SET {field} = ? WHERE customer_id = ?",
            (normalized_value, customer_id),
        )
    # 성공 메시지를 반환합니다.
    return f"SQLite에서 {customer_id}의 '{field}'을(를) '{value}'(으)로 저장했습니다."


@tool
def get_profile(customer_id: str) -> str:
    """고객 ID로 JSON 장기 기억 프로필을 조회합니다."""
    # JSON 저장소에서 고객 프로필을 조회합니다.
    profile = read_json_profile(customer_id)
    # 고객이 없으면 안전한 안내 문자열을 반환합니다.
    if profile is None:
        # 존재하지 않는 고객 ID임을 알려줍니다.
        return f"{customer_id} 프로필이 없습니다."
    # 에이전트가 이해할 수 있도록 프로필 딕셔너리를 한글 JSON 문자열로 반환합니다.
    return json.dumps(profile, ensure_ascii=False)


@tool
def update_profile(customer_id: str, field: str, value: str) -> str:
    """고객 프로필의 한 필드를 JSON 파일에 영속 저장합니다."""
    # 실제 저장 로직을 공통 함수에 위임합니다.
    return write_json_profile(customer_id, field, value)


@tool
def get_profile_sqlite(customer_id: str) -> str:
    """고객 ID로 SQLite 장기 기억 프로필을 조회합니다."""
    # SQLite 저장소에서 고객 프로필을 조회합니다.
    profile = read_sqlite_profile(customer_id)
    # 고객이 없으면 안내 문자열을 반환합니다.
    if profile is None:
        # 조회 실패를 예외 대신 안전한 메시지로 처리합니다.
        return f"{customer_id} 프로필이 없습니다."
    # 프로필 딕셔너리를 한글 JSON 문자열로 변환해 에이전트에 반환합니다.
    return json.dumps(profile, ensure_ascii=False)


@tool
def update_profile_sqlite(customer_id: str, field: str, value: str) -> str:
    """고객 프로필의 한 필드를 SQLite에 영속 저장합니다."""
    # 검증과 SQL 실행을 담당하는 공통 함수에 처리를 위임합니다.
    return write_sqlite_profile(customer_id, field, value)
