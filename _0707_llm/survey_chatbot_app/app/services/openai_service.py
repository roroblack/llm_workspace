# 앱 설정값을 가져옵니다.
from app.core.config import ENABLE_OPENAI, OPENAI_API_KEY, OPENAI_MODEL, SURVEY_LINK

# 비용 보호를 위해 ENABLE_OPENAI=true인 경우에만 OpenAI 클라이언트를 생성합니다.
client = None
if ENABLE_OPENAI and OPENAI_API_KEY:
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)

# OpenAI 답변을 생성하는 함수입니다.
def generate_openai_reply(user_message: str, intent: str, bot_context: str) -> str:
    # API 사용이 비활성화된 경우 키가 있어도 OpenAI API를 호출하지 않습니다.
    if not ENABLE_OPENAI:
        return f"{bot_context}\n\n※ OpenAI API 사용이 비활성화되어 기본 응답으로 표시합니다."

    # API Key가 없는 경우에도 앱이 오류 없이 동작하도록 기본 답변을 반환합니다.
    if client is None:
        # 실습 환경에서 API Key 미설정 시 표시할 안내 문장입니다.
        return f"{bot_context}\n\n※ OPENAI_API_KEY가 설정되지 않아 기본 응답으로 표시합니다."

    # 시스템 역할 메시지입니다.
    system_prompt = (
        "너는 설문조사 진행을 도와주는 한국어 AI 챗봇이다. "
        "사용자의 답변을 자연스럽게 받고, 다음 질문을 안내한다. "
        "응답은 짧고 친절하게 작성한다. "
        f"설문 링크가 필요하면 다음 링크를 안내한다: {SURVEY_LINK}"
    )

    # OpenAI Chat Completions API를 호출합니다.
    response = client.chat.completions.create(
        # 사용할 모델명을 지정합니다.
        model=OPENAI_MODEL,
        # 챗봇 대화 메시지 목록입니다.
        messages=[
            # 챗봇의 역할과 규칙입니다.
            {"role": "system", "content": system_prompt},
            # 현재 설문 진행 상태입니다.
            {"role": "assistant", "content": bot_context},
            # 사용자의 실제 입력입니다.
            {"role": "user", "content": f"의도: {intent}\n입력: {user_message}"},
        ],
        # 답변이 너무 길어지지 않도록 최대 토큰 수를 제한합니다.
        max_tokens=400,
        # 답변의 창의성을 적당히 유지합니다.
        temperature=0.4,
    )

    # 첫 번째 응답 메시지의 텍스트를 반환합니다.
    return response.choices[0].message.content or bot_context
