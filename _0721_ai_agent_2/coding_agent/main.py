# -*- coding: utf-8 -*-
"""PDF 1~19페이지의 'Coding agent' 실습을 실행 가능한 CLI로 구현한다.

흐름: 원본 읽기 -> LLM 수정 요청 -> 코드블록 추출 -> 새 파일 저장
      -> 별도 프로세스 실행 -> 종료 코드로 검증

LLM이 만든 코드를 실제로 실행하므로 신뢰할 수 있는 로컬 코드에만 사용하고,
생성된 수정본은 사람이 검토한 뒤 반영해야 한다.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import re
import subprocess
import sys
from typing import Any

from dotenv import load_dotenv


ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / "data"
TARGET = DATA / "buggy_script.py"
FIXED = DATA / "fixed_script.py"
DEFAULT_TIMEOUT = 60


class ConfigurationError(RuntimeError):
    """API 키나 LLM 설정이 준비되지 않았을 때 발생한다."""


def read_code(path: pathlib.Path) -> str:
    """대상 소스코드를 UTF-8 문자열로 읽는다."""
    path = path.expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(
            f"대상 파일이 없습니다: {path}\n"
            "--target 옵션으로 수정할 파이썬 파일을 지정하세요."
        )
    return path.read_text(encoding="utf-8")


def extract_code(text: str) -> str:
    """LLM 응답에서 첫 번째 Python 코드블록만 추출한다.

    코드블록이 없는 응답은 PDF 예제와 마찬가지로 전체 응답을 반환한다.
    """
    match = re.search(r"```(?:python)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    return (match.group(1) if match else text).strip()


def _content_to_text(content: Any) -> str:
    """LangChain 공급자별 응답 content를 일반 문자열로 변환한다."""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return str(content)

    parts: list[str] = []
    for item in content:
        if isinstance(item, str):
            parts.append(item)
        elif isinstance(item, dict):
            value = item.get("text") or item.get("content")
            if value:
                parts.append(str(value))
        else:
            value = getattr(item, "text", None)
            if value:
                parts.append(str(value))
    return "\n".join(parts)


def get_llm(provider: str = "gemini", temperature: float = 0.0):
    """환경변수에 설정된 OpenAI 또는 Gemini 채팅 모델을 만든다."""
    load_dotenv(ROOT / ".env")
    provider = provider.lower()

    if provider == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY", "").strip()
        if (
            not api_key
            or api_key.startswith("여기에")
            or "API_KEY" in api_key.upper()
        ):
            raise ConfigurationError(
                "GOOGLE_API_KEY가 없습니다. .env.example을 .env로 복사한 뒤 "
                "키를 입력하거나 --provider openai를 사용하세요."
            )
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            temperature=temperature,
            google_api_key=api_key,
        )

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if (
            not api_key
            or api_key.startswith("여기에")
            or "API_KEY" in api_key.upper()
        ):
            raise ConfigurationError(
                "OPENAI_API_KEY가 없습니다. .env.example을 .env로 복사한 뒤 "
                "키를 입력하거나 --provider gemini를 사용하세요."
            )
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=temperature,
            api_key=api_key,
        )

    raise ConfigurationError(f"지원하지 않는 LLM 공급자입니다: {provider}")


def ask_fix(source: str, llm: Any | None = None, provider: str = "gemini") -> str:
    """LLM에 버그를 고친 전체 코드를 요청하고 순수 코드만 반환한다."""
    llm = llm or get_llm(provider, temperature=0.0)
    prompt = (
        "다음 파이썬 스크립트에는 버그가 있다. 버그를 모두 찾아 고친 "
        "전체 코드를 하나의 코드블록으로만 출력하라. 설명 또는 코드블록 밖의 "
        "텍스트는 쓰지 마라.\n"
        "주의: 한글 CSV 인코딩, 문자열/정수 타입 변환, 숫자 비교를 점검하라.\n\n"
        f"```python\n{source}\n```"
    )
    response = llm.invoke(prompt)
    text = _content_to_text(getattr(response, "content", response))
    code = extract_code(text)
    if not code:
        raise ValueError("LLM이 빈 수정본을 반환했습니다.")
    return code


def _working_directory(target: pathlib.Path) -> pathlib.Path:
    """대상 파일의 상대경로가 올바르게 동작할 프로젝트 루트를 추정한다."""
    target = target.expanduser().resolve()
    if target.parent.name.lower() == "data":
        return target.parent.parent
    return target.parent


def save_and_run(
    code: str,
    fixed: pathlib.Path = FIXED,
    *,
    cwd: pathlib.Path = ROOT,
    timeout: int = DEFAULT_TIMEOUT,
) -> tuple[int, str]:
    """수정 코드를 새 파일에 저장하고 별도 프로세스로 실행한다."""
    fixed = fixed.expanduser().resolve()
    cwd = cwd.expanduser().resolve()
    fixed.parent.mkdir(parents=True, exist_ok=True)
    fixed.write_text(code.rstrip() + "\n", encoding="utf-8")

    # 자식 Python과 현재 프로세스 사이의 한글 입출력을 UTF-8로 통일한다.
    child_env = os.environ.copy()
    child_env["PYTHONUTF8"] = "1"
    proc = subprocess.run(
        [sys.executable, str(fixed)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        env=child_env,
        check=False,
    )
    return proc.returncode, proc.stdout + proc.stderr


def fix_file(
    path: pathlib.Path,
    fixed: pathlib.Path | None = None,
    *,
    provider: str = "gemini",
    timeout: int = DEFAULT_TIMEOUT,
    llm: Any | None = None,
) -> tuple[bool, int, str, pathlib.Path]:
    """파일 하나를 고쳐 새 파일로 저장하고 실행 결과를 반환한다."""
    path = path.expanduser().resolve()
    fixed = (fixed or path.with_name("fixed_script.py")).expanduser().resolve()
    if path == fixed:
        raise ValueError("원본 보존을 위해 --fixed는 --target과 달라야 합니다.")

    source = read_code(path)
    fixed_code = ask_fix(source, llm=llm, provider=provider)
    return_code, output = save_and_run(
        fixed_code,
        fixed,
        cwd=_working_directory(path),
        timeout=timeout,
    )
    return return_code == 0, return_code, output, fixed


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="LLM이 Python 코드를 수정하고 subprocess 실행으로 검증합니다."
    )
    parser.add_argument(
        "--target",
        type=pathlib.Path,
        default=TARGET,
        help=f"수정할 원본 파일 (기본값: {TARGET})",
    )
    parser.add_argument(
        "--fixed",
        type=pathlib.Path,
        default=None,
        help="수정본 저장 경로 (기본값: 원본과 같은 폴더의 fixed_script.py)",
    )
    parser.add_argument(
        "--provider",
        choices=("gemini", "openai"),
        default=os.getenv("LLM_PROVIDER", "gemini"),
        help="사용할 LLM 공급자 (기본값: gemini)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"수정본 실행 제한 시간(초, 기본값: {DEFAULT_TIMEOUT})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.timeout <= 0:
        print("[입력 오류] --timeout은 1 이상의 정수여야 합니다.", file=sys.stderr)
        return 2

    target = args.target.expanduser().resolve()
    fixed = (args.fixed or target.with_name("fixed_script.py")).expanduser().resolve()

    print(f"[1] 원본 코드 읽기: {target}")
    print(f"[2] {args.provider.upper()}에 버그 수정 요청")
    print(f"[3] 새 파일 저장 후 실행 검증: {fixed}")
    print("-" * 72)

    try:
        success, return_code, output, saved_path = fix_file(
            target,
            fixed,
            provider=args.provider,
            timeout=args.timeout,
        )
    except (ConfigurationError, FileNotFoundError, ValueError) as error:
        print(f"[실행 준비 오류] {error}", file=sys.stderr)
        return 2
    except subprocess.TimeoutExpired:
        print(
            f"[실행 실패] 수정본이 {args.timeout}초 안에 끝나지 않아 종료했습니다.",
            file=sys.stderr,
        )
        return 1
    except Exception as error:
        print(f"[예상하지 못한 오류] {type(error).__name__}: {error}", file=sys.stderr)
        return 1

    print(f"[실행 결과] 종료코드: {return_code} (0=정상)")
    if output:
        print(output.rstrip())
    print("-" * 72)
    if success:
        print(f"성공: 수정본이 정상 동작합니다. 사람이 검토하세요: {saved_path}")
        return 0

    print(
        "실패: 오류 출력을 LLM에 다시 전달해 재수정해야 합니다 "
        "(PDF 20페이지 이후의 재귀 수정 단계).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
