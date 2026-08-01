"""프롬프트에서 MNIST 생성 대상 숫자를 추출합니다."""

# 숫자 패턴 검색을 위해 정규표현식 모듈을 가져옵니다.
import re

# 한글과 영어 숫자 표현을 실제 숫자값으로 연결합니다.
DIGIT_WORDS = {
    "영": 0, "공": 0, "zero": 0,
    "일": 1, "하나": 1, "one": 1,
    "이": 2, "둘": 2, "two": 2,
    "삼": 3, "셋": 3, "three": 3,
    "사": 4, "넷": 4, "four": 4,
    "오": 5, "다섯": 5, "five": 5,
    "육": 6, "여섯": 6, "six": 6,
    "칠": 7, "일곱": 7, "seven": 7,
    "팔": 8, "여덟": 8, "eight": 8,
    "구": 9, "아홉": 9, "nine": 9,
}


def extract_target_digit(prompt: str) -> tuple[int, str]:
    """프롬프트에서 0~9 숫자를 찾아 숫자값과 정규화 문장을 반환합니다."""
    # 앞뒤 공백을 제거합니다.
    cleaned_prompt = prompt.strip()
    # 한 자리 숫자 문자를 검색합니다.
    digit_match = re.search(r"(?<!\d)([0-9])(?!\d)", cleaned_prompt)
    # 숫자 문자를 찾았는지 확인합니다.
    if digit_match is not None:
        # 찾은 문자를 정수로 변환합니다.
        target_digit = int(digit_match.group(1))
        # 실제 모델 조건을 명확하게 설명하는 문장을 생성합니다.
        return target_digit, f"{cleaned_prompt} → MNIST 숫자 {target_digit} 생성"
    # 영어 비교를 위해 소문자로 변환합니다.
    lowered_prompt = cleaned_prompt.lower()
    # 등록된 숫자 단어를 순서대로 확인합니다.
    for word, value in DIGIT_WORDS.items():
        # 숫자 단어가 문장에 포함되는지 확인합니다.
        if word in lowered_prompt:
            # 찾은 숫자와 정규화 문장을 반환합니다.
            return value, f"{cleaned_prompt} → MNIST 숫자 {value} 생성"
    # 숫자 표현이 없으면 입력 오류를 발생시킵니다.
    raise ValueError("프롬프트에 숫자 0~9 또는 숫자 단어를 포함하세요. 예: 숫자 7을 생성해 주세요.")
