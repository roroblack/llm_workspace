# -*- coding: utf-8 -*-
"""외부 API나 LangGraph 설치 없이도 테스트할 수 있는 순수 파이썬 규칙 모듈입니다."""

# LLM이 반환할 수 있는 허용 카테고리를 한 곳에 정의합니다.
CATEGORIES = ["결제", "배송", "환불", "교환", "회원", "기술지원", "기타"]

# 긴급 우선순위 판단에 사용할 핵심 단어 목록입니다.
URGENT_WORDS = ["결제", "오류", "안 돼", "안돼", "파손", "안와", "안 와", "먹통"]

# 높은 우선순위 판단에 사용할 핵심 단어 목록입니다.
HIGH_WORDS = ["환불", "교환", "튕", "취소"]

# 카테고리를 실제 담당팀으로 변환하기 위한 매핑표입니다.
TEAM_MAP = {
    "결제": "결제지원팀",
    "환불": "정산팀",
    "교환": "물류팀",
    "배송": "물류팀",
    "회원": "회원관리팀",
    "기술지원": "기술지원팀",
}


def normalize_category(raw_output: str) -> tuple[str, str]:
    """LLM 출력에서 허용 카테고리를 검증하고 보정 결과와 오류를 반환합니다."""

    # 모델 출력의 앞뒤 공백과 줄바꿈을 제거합니다.
    cleaned_output = raw_output.strip()

    # 출력이 허용 목록의 단어와 정확히 일치하면 정상 결과로 채택합니다.
    if cleaned_output in CATEGORIES:
        return cleaned_output, ""

    # 설명 문장 속에 허용 카테고리가 섞여 있으면 해당 단어를 추출합니다.
    for category in CATEGORIES:
        # 현재 카테고리 단어가 모델 출력에 포함되어 있는지 검사합니다.
        if category in cleaned_output:
            return category, ""

    # 빈 문자열이거나 허용 범위 밖이면 오류 메시지에 사용할 미리보기를 만듭니다.
    preview = cleaned_output[:30] if cleaned_output else "빈 응답"

    # 안전한 기본값인 기타와 추적 가능한 검증 오류 메시지를 반환합니다.
    return "기타", f"분류값 미허용('{preview}') → 기타 보정"


def calculate_priority(content: str, category: str) -> str:
    """티켓 내용과 카테고리를 이용하여 규칙 기반 우선순위를 계산합니다."""

    # 결제 카테고리 또는 긴급 단어가 있으면 긴급으로 판정합니다.
    if category == "결제" or any(word in content for word in URGENT_WORDS):
        return "긴급"

    # 환불·교환 카테고리 또는 높은 우선순위 단어가 있으면 높음으로 판정합니다.
    if category in ("환불", "교환") or any(word in content for word in HIGH_WORDS):
        return "높음"

    # 그 외 일반 문의는 보통으로 판정합니다.
    return "보통"


def calculate_team(category: str) -> str:
    """카테고리에 맞는 담당팀을 반환하고 미등록 카테고리는 일반상담팀으로 보냅니다."""

    # 딕셔너리에 카테고리가 있으면 해당 팀을, 없으면 일반상담팀을 반환합니다.
    return TEAM_MAP.get(category, "일반상담팀")


def calculate_route(priority: str) -> str:
    """우선순위에 따라 조건부 그래프가 이동할 경로 이름을 반환합니다."""

    # 긴급은 알림 노드로, 나머지는 바로 일반 배정 노드로 라우팅합니다.
    return "notify" if priority == "긴급" else "assign"
