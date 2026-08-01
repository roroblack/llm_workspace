"""
로컬 JSON 파일에 일정을 저장하는 Calendar Tool 어댑터입니다.
"""

# JSON 파일을 읽고 쓰기 위해 json을 가져옵니다.
import json

# 날짜와 시간 문자열 검증을 위해 datetime을 가져옵니다.
from datetime import datetime

# 파일 경로 처리를 위해 Path를 가져옵니다.
from pathlib import Path

# 일정 고유 ID를 생성하기 위해 uuid4를 가져옵니다.
from uuid import uuid4


# 캘린더 어댑터를 정의합니다.
class CalendarAdapter:
    """외부 계정 없이 실행 가능한 로컬 캘린더 저장소입니다."""

    # 일정 JSON 파일 경로를 전달받습니다.
    def __init__(self, calendar_file: Path) -> None:
        # 파일 경로를 저장합니다.
        self.calendar_file = calendar_file

        # 상위 폴더가 없으면 생성합니다.
        self.calendar_file.parent.mkdir(parents=True, exist_ok=True)

        # 파일이 없으면 빈 일정 배열을 저장합니다.
        if not self.calendar_file.exists():
            self.calendar_file.write_text("[]", encoding="utf-8")

    # 전체 일정을 읽습니다.
    def _load(self) -> list[dict]:
        """JSON 파일의 일정 목록을 반환합니다."""

        # UTF-8로 JSON 문자열을 읽어 Python 목록으로 변환합니다.
        return json.loads(self.calendar_file.read_text(encoding="utf-8"))

    # 전체 일정을 저장합니다.
    def _save(self, events: list[dict]) -> None:
        """일정 목록을 JSON 파일에 저장합니다."""

        # 한글을 유지하고 읽기 쉽게 들여쓰기하여 저장합니다.
        self.calendar_file.write_text(
            json.dumps(events, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # 새 일정을 생성합니다.
    def create_event(self, title: str, start: str, end: str, description: str = "") -> dict:
        """ISO 8601 문자열을 검증하고 새 일정을 저장합니다."""

        # 시작 시간을 파싱하여 형식을 검증합니다.
        start_dt = datetime.fromisoformat(start)

        # 종료 시간을 파싱하여 형식을 검증합니다.
        end_dt = datetime.fromisoformat(end)

        # 종료 시간이 시작 시간보다 빠르면 오류를 발생시킵니다.
        if end_dt <= start_dt:
            raise ValueError("종료 시간은 시작 시간보다 늦어야 합니다.")

        # 기존 일정을 읽습니다.
        events = self._load()

        # 새 일정 딕셔너리를 생성합니다.
        event = {
            "id": str(uuid4()),
            "title": title,
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat(),
            "description": description,
        }

        # 새 일정을 목록에 추가합니다.
        events.append(event)

        # 시작 시간 순으로 정렬합니다.
        events.sort(key=lambda item: item["start"])

        # 변경된 목록을 저장합니다.
        self._save(events)

        # 생성된 일정을 반환합니다.
        return event

    # 일정 목록을 반환합니다.
    def list_events(self) -> list[dict]:
        """저장된 전체 일정을 시간 순으로 반환합니다."""

        # 일정을 읽고 시작 시간 순으로 정렬하여 반환합니다.
        return sorted(self._load(), key=lambda item: item["start"])
