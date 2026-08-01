# 기능 유형별 프롬프트를 생성하는 함수입니다.
def build_prompt(task_type: str, user_prompt: str) -> str:
    # task_type 값을 소문자로 통일하여 비교 오류를 줄입니다.
    task = task_type.lower().strip()

    # 문장 생성 기능 프롬프트입니다.
    if task == "sentence":
        return f"""
다음 주제에 맞는 자연스러운 문장을 생성하시오.

주제:
{user_prompt}
"""

    # 질의 응답 기능 프롬프트입니다.
    if task == "qa":
        return f"""
다음 질문에 대해 핵심 개념, 이유, 예시를 포함하여 답변하시오.

질문:
{user_prompt}
"""

    # 요약 기능 프롬프트입니다.
    if task == "summary":
        return f"""
다음 내용을 핵심 중심으로 요약하시오.
가능하면 3~5개의 문장으로 정리하시오.

내용:
{user_prompt}
"""

    # 번역 기능 프롬프트입니다.
    if task == "translation":
        return f"""
다음 문장을 자연스럽게 번역하시오.
한국어이면 영어로, 영어이면 한국어로 번역하시오.

문장:
{user_prompt}
"""

    # 채팅 기능 프롬프트입니다.
    if task == "chat":
        return f"""
사용자와 자연스럽게 대화하시오.
이전 대화 맥락이 있다면 참고하여 답변하시오.

사용자 입력:
{user_prompt}
"""

    # 다양한 Use Case 기능 프롬프트입니다.
    if task == "usecase":
        return f"""
다음 요구사항을 실제 업무 활용 사례처럼 처리하시오.
필요하면 결과물 형식까지 갖추어 작성하시오.

요구사항:
{user_prompt}
"""

    # 알 수 없는 task_type이면 기본 질의응답 방식으로 처리합니다.
    return f"""
다음 요청을 분석하여 적절한 답변을 작성하시오.

요청:
{user_prompt}
"""
