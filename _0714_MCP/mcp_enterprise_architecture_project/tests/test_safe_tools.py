"""핵심 로컬 Tool의 안전성과 기본 동작을 검사합니다."""

# 임시 경로 fixture를 사용하기 위해 pytest를 가져옵니다.
import pytest

# 테스트할 어댑터를 가져옵니다.
from external_systems.file_system import FileSystemAdapter
from external_systems.python_sandbox import PythonSandboxAdapter


# Python 계산 Tool의 정상 계산을 검사합니다.
def test_python_calculate() -> None:
    """기본 산술 표현식을 정확히 계산해야 합니다."""

    # 계산 어댑터를 생성합니다.
    adapter = PythonSandboxAdapter()

    # 식을 계산합니다.
    result = adapter.evaluate("(12 + 8) * 3")

    # 결과가 60인지 검사합니다.
    assert result["result"] == 60


# Python Tool에서 함수 호출과 import가 차단되는지 검사합니다.
def test_python_blocks_function_call() -> None:
    """임의 함수 호출은 거부되어야 합니다."""

    # 계산 어댑터를 생성합니다.
    adapter = PythonSandboxAdapter()

    # 금지된 함수 호출이 ValueError를 발생시키는지 검사합니다.
    with pytest.raises(ValueError):
        adapter.evaluate("__import__('os').system('dir')")


# File Tool의 경로 탈출 방지를 검사합니다.
def test_file_path_escape_is_blocked(tmp_path) -> None:
    """기준 폴더 밖의 경로 접근은 거부되어야 합니다."""

    # 임시 폴더를 기준으로 파일 어댑터를 생성합니다.
    adapter = FileSystemAdapter(tmp_path / "safe")

    # 상위 폴더 접근이 ValueError를 발생시키는지 검사합니다.
    with pytest.raises(ValueError):
        adapter.read_text("../secret.txt")
