# -*- coding: utf-8 -*-
"""콘솔에서 값을 입력받고 결과를 보기 좋게 출력하는 보조 파일입니다."""


def print_header(title: str) -> None:
    """구분선과 함께 화면 상단에 제목을 출력합니다."""

    # 제목을 감싸는 구분선을 출력합니다.
    print("=" * 60)

    # 가운데에 제목 문구를 출력합니다.
    print(title)

    # 제목 아래쪽 구분선을 출력합니다.
    print("=" * 60)


def print_result(model_name: str, answer: str) -> None:
    """모델 이름과 생성된 답변을 정돈된 형태로 출력합니다."""

    # 어떤 모델의 답변인지 알려주는 머리말을 출력합니다.
    print(f"\n[{model_name} 응답]")

    # 답변 위쪽 구분선을 출력합니다.
    print("-" * 60)

    # 실제 생성된 답변을 출력합니다.
    print(answer)

    # 답변 아래쪽 구분선을 출력합니다.
    print("-" * 60)


def ask_float(prompt: str, default: float, low: float, high: float) -> float:
    """실수 값을 입력받되 허용 범위를 벗어나면 다시 입력받습니다."""

    # 올바른 값이 들어올 때까지 반복해서 입력을 받습니다.
    while True:
        # 기본값을 안내하며 사용자 입력을 문자열로 받습니다.
        raw = input(f"{prompt} (기본값 {default}, 범위 {low}~{high}): ").strip()

        # 아무것도 입력하지 않으면 기본값을 그대로 사용합니다.
        if not raw:
            return default

        # 숫자로 변환을 시도하고, 실패하면 안내 후 다시 입력받습니다.
        try:
            value = float(raw)
        except ValueError:
            print("숫자 형태로 입력해 주세요.")
            continue

        # 허용 범위를 벗어나면 안내 후 다시 입력받습니다.
        if value < low or value > high:
            print(f"{low}부터 {high} 사이의 값을 입력해 주세요.")
            continue

        # 조건을 모두 통과한 값을 반환합니다.
        return value


def ask_int(prompt: str, default: int, low: int, high: int) -> int:
    """정수 값을 입력받되 허용 범위를 벗어나면 다시 입력받습니다."""

    # 올바른 값이 들어올 때까지 반복해서 입력을 받습니다.
    while True:
        # 기본값을 안내하며 사용자 입력을 문자열로 받습니다.
        raw = input(f"{prompt} (기본값 {default}, 범위 {low}~{high}): ").strip()

        # 아무것도 입력하지 않으면 기본값을 그대로 사용합니다.
        if not raw:
            return default

        # 정수로 변환을 시도하고, 실패하면 안내 후 다시 입력받습니다.
        try:
            value = int(raw)
        except ValueError:
            print("정수 형태로 입력해 주세요.")
            continue

        # 허용 범위를 벗어나면 안내 후 다시 입력받습니다.
        if value < low or value > high:
            print(f"{low}부터 {high} 사이의 값을 입력해 주세요.")
            continue

        # 조건을 모두 통과한 값을 반환합니다.
        return value
