# -*- coding: utf-8 -*-
"""제23강 HTML의 실습문제 해답을 실행 가능한 함수로 구현한 모듈입니다."""

from pathlib import Path

from common import DATA
from coding_agent import (
    DEFAULT_FIXED,
    DEFAULT_TARGET,
    ask_fix_with_summary,
    read_code,
    run_code,
    save_code,
    self_debug,
)


def exercise_summary(provider: str) -> None:
    """실습 1: 변경 요약은 콘솔에, 수정 코드는 새 파일에 분리 저장합니다."""
    source = read_code(DEFAULT_TARGET)
    code, summary = ask_fix_with_summary(source, provider)
    save_code(code, DEFAULT_FIXED)
    result = run_code(DEFAULT_FIXED)
    print("\n[변경 요약]")
    print(summary or "LLM이 별도 요약을 반환하지 않았습니다.")
    print("\n[실행 검증]")
    print(f"종료코드: {result.returncode} (0=정상)")
    print(result.combined_output)


def create_my_buggy_script() -> Path:
    """실습 2에서 사용할 0 나누기와 잘못된 인덱싱 버그 파일을 생성합니다."""
    target = DATA / "my_buggy.py"
    source = '''# -*- coding: utf-8 -*-
"""실습을 위해 의도적으로 두 가지 런타임 버그를 포함한 파일입니다."""

numbers = [10, 20, 30]
empty = []

# 버그 1: 빈 리스트 길이는 0이므로 ZeroDivisionError가 발생합니다.
print("빈 목록 평균:", sum(empty) / len(empty))

# 버그 2: numbers에는 인덱스 0~2만 있으므로 IndexError가 발생합니다.
print("여섯 번째 값:", numbers[5])
'''
    target.write_text(source, encoding="utf-8")
    return target


def exercise_custom_bug(provider: str) -> None:
    """실습 2: 새 버그 파일을 만든 뒤 self-debugging으로 정상 종료까지 시도합니다."""
    target = create_my_buggy_script()
    destination = DATA / "my_buggy_fixed.py"
    success, history, _latest = self_debug(target, destination, provider, max_tries=3)
    for index, result in enumerate(history, start=1):
        print(f"\n[시도 {index}] 종료코드: {result.returncode}")
        print(result.combined_output)
    print("\n최종 결과:", "성공" if success else "실패 — 사람의 검토가 필요합니다.")
    print("수정본:", destination)
