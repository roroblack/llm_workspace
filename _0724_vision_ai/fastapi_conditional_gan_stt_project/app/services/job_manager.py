"""백그라운드 GAN 작업의 상태를 메모리에서 관리합니다."""

# 여러 스레드의 안전한 접근을 위해 Lock을 가져옵니다.
from threading import Lock
# 다양한 상태값 타입을 표현하기 위해 Any를 가져옵니다.
from typing import Any


# 작업 상태 저장소를 정의합니다.
class JobManager:
    """작업 ID별 상태, 진행률, 이미지 URL을 저장합니다."""

    def __init__(self) -> None:
        # 작업 상태 딕셔너리를 생성합니다.
        self._jobs: dict[str, dict[str, Any]] = {}
        # 동시 접근 제어용 잠금 객체를 생성합니다.
        self._lock = Lock()

    def create(self, job_id: str, initial_data: dict[str, Any]) -> None:
        # 잠금 범위 안에서 새 작업을 등록합니다.
        with self._lock:
            # 외부 객체 변경의 영향을 막기 위해 복사본을 저장합니다.
            self._jobs[job_id] = dict(initial_data)

    def update(self, job_id: str, **changes: Any) -> None:
        # 잠금 범위 안에서 작업 상태를 변경합니다.
        with self._lock:
            # 존재하지 않는 작업인지 확인합니다.
            if job_id not in self._jobs:
                # 잘못된 작업 ID이면 예외를 발생시킵니다.
                raise KeyError(f"존재하지 않는 작업 ID입니다: {job_id}")
            # 전달받은 변경값을 기존 상태에 반영합니다.
            self._jobs[job_id].update(changes)

    def get(self, job_id: str) -> dict[str, Any] | None:
        # 잠금 범위 안에서 작업 상태를 읽습니다.
        with self._lock:
            # 작업이 없으면 None을 반환합니다.
            if job_id not in self._jobs:
                return None
            # 외부 수정 방지를 위해 복사본을 반환합니다.
            return dict(self._jobs[job_id])


# 애플리케이션 전체에서 공유할 작업 관리자 객체를 생성합니다.
job_manager = JobManager()
