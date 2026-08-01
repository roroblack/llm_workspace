# -*- coding: utf-8 -*-
"""코드 읽기 → LLM 수정 → 새 파일 저장 → 격리 실행을 담당하는 핵심 모듈입니다."""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# 같은 code 폴더의 공통 모듈을 사용합니다.
from common import DATA, ROOT, get_chat


# 원본 파일은 절대 덮어쓰지 않고 비교 기준으로 보존합니다.
DEFAULT_TARGET: Path = DATA / "buggy_script.py"
# 일반 1회 수정 결과를 저장할 별도 파일입니다.
DEFAULT_FIXED: Path = DATA / "fixed_script.py"
# 재귀적 수정 결과는 다시 별도 파일에 저장해 실습 결과끼리 충돌하지 않게 합니다.
LOOP_FIXED: Path = DATA / "fixed_script_loop.py"


@dataclass
class RunResult:
    """수정 코드 실행 결과를 구조화해 전달하는 데이터 클래스입니다."""

    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def combined_output(self) -> str:
        """정상 출력과 오류 출력을 한 번에 확인할 수 있게 합쳐 반환합니다."""
        return (self.stdout + self.stderr).strip()

    @property
    def success(self) -> bool:
        """종료코드가 0이고 타임아웃이 아니면 정상 실행으로 판정합니다."""
        return self.returncode == 0 and not self.timed_out


def read_code(path: Path) -> str:
    """UTF-8 인코딩으로 파이썬 소스 파일 전체를 읽습니다."""
    if not path.exists():
        raise FileNotFoundError(f"대상 코드 파일이 없습니다: {path}")
    return path.read_text(encoding="utf-8")


def extract_code(text: str) -> str:
    """LLM 응답에서 첫 번째 Python 코드블록의 내부 코드만 추출합니다."""
    # re.DOTALL을 사용해 점(.)이 줄바꿈까지 포함하도록 하여 여러 줄 코드를 추출합니다.
    match = re.search(r"```(?:python)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    # 코드블록이 있으면 내부만, 없으면 모델 응답 전체를 코드 후보로 사용합니다.
    code = match.group(1) if match else text
    return code.strip()


def remove_code_blocks(text: str) -> str:
    """사람에게 보여 줄 변경 요약을 얻기 위해 코드블록을 응답에서 제거합니다."""
    return re.sub(r"```(?:python)?\s*.*?```", "", text, flags=re.DOTALL | re.IGNORECASE).strip()


def ask_fix(source: str, provider: str, error: str = "") -> str:
    """원본 코드와 선택적 실행 오류를 LLM에 전달해 수정된 전체 코드를 받습니다."""
    # 코드 수정은 창의성보다 일관성과 정확성이 중요하므로 temperature를 0으로 둡니다.
    llm = get_chat(provider=provider, temperature=0.0)
    # 두 번째 시도부터는 실제 실행 오류를 포함해 추측이 아닌 표적 수정을 유도합니다.
    feedback = ""
    if error:
        feedback = (
            "\n\n[직전 실행 오류]\n"
            f"{error[:2000]}\n"
            "위 오류가 사라지도록 수정하라.\n"
        )
    prompt = (
        "다음 파이썬 스크립트의 버그를 모두 고쳐라. "
        "수정된 실행 가능한 전체 코드만 하나의 ```python 코드블록```으로 출력하라. "
        "코드블록 밖의 설명은 쓰지 마라. "
        "CSV 한글 인코딩, 문자열을 숫자로 변환하는 처리, 숫자 비교, 파일 상대경로를 점검하라. "
        "원본 데이터 파일을 삭제하거나 수정하는 코드는 만들지 마라."
        f"{feedback}\n```python\n{source}\n```"
    )
    response = llm.invoke(prompt)
    # LangChain 메시지의 content 속성을 문자열로 바꾸어 공급자 차이를 흡수합니다.
    response_text = str(getattr(response, "content", response))
    return extract_code(response_text)


def ask_fix_with_summary(source: str, provider: str) -> tuple[str, str]:
    """수정 코드와 사람이 검토할 변경 요약을 동시에 생성해 분리 반환합니다."""
    llm = get_chat(provider=provider, temperature=0.0)
    prompt = (
        "다음 파이썬 스크립트의 버그를 모두 고쳐라. "
        "먼저 '### 변경 요약' 제목 아래에 무엇을 왜 고쳤는지 번호로 설명하고, "
        "그 다음 수정된 실행 가능한 전체 코드를 하나의 ```python 코드블록```으로 출력하라. "
        "CSV 인코딩, 문자열 합산, 문자열 숫자 비교를 반드시 점검하라.\n\n"
        f"```python\n{source}\n```"
    )
    response = llm.invoke(prompt)
    response_text = str(getattr(response, "content", response))
    # 저장 파일에는 순수 코드만 들어가도록 추출합니다.
    code = extract_code(response_text)
    # 코드블록 바깥 텍스트는 검토용 요약으로 콘솔에만 표시합니다.
    summary = remove_code_blocks(response_text)
    return code, summary


def save_code(code: str, destination: Path) -> Path:
    """수정 코드를 원본이 아닌 새 파일에 UTF-8로 저장합니다."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(code.rstrip() + "\n", encoding="utf-8")
    return destination


def run_code(path: Path, timeout_seconds: int = 20) -> RunResult:
    """현재 가상환경의 Python으로 코드를 별도 프로세스에서 안전하게 실행합니다."""
    try:
        process = subprocess.run(
            [sys.executable, str(path)],
            # buggy_script.py가 data/sales_daily.csv 상대경로를 사용하므로 프로젝트 루트에서 실행합니다.
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
        return RunResult(process.returncode, process.stdout, process.stderr)
    except subprocess.TimeoutExpired as exc:
        # 무한루프 가능성을 차단하고 앱 자체는 계속 실행되게 합니다.
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return RunResult(124, stdout, stderr + "\n[타임아웃] 제한 시간을 초과했습니다.", True)


def fix_once(target: Path, destination: Path, provider: str) -> tuple[str, RunResult]:
    """대상 코드를 한 번 수정하고 새 파일에 저장한 뒤 실제 실행해 검증합니다."""
    source = read_code(target)
    fixed_code = ask_fix(source, provider)
    save_code(fixed_code, destination)
    return fixed_code, run_code(destination)


def self_debug(
    target: Path,
    destination: Path,
    provider: str,
    max_tries: int = 3,
) -> tuple[bool, list[RunResult], str]:
    """오류 피드백을 이용해 최대 횟수까지 수정·실행을 반복합니다."""
    source = read_code(target)
    error = ""
    history: list[RunResult] = []
    latest_code = source

    # 반드시 상한을 두어 API 비용과 무한 재시도를 방지합니다.
    for _attempt in range(1, max_tries + 1):
        latest_code = ask_fix(source=source, provider=provider, error=error)
        save_code(latest_code, destination)
        result = run_code(destination)
        history.append(result)
        if result.success:
            return True, history, latest_code
        # 다음 시도는 직전 수정본과 실제 실행 오류를 함께 사용해 누적 개선합니다.
        source = latest_code
        error = result.combined_output

    return False, history, latest_code
