# 운영체제 환경변수를 읽기 위해 os 모듈을 불러옵니다.
import os
# .env 파일의 환경변수를 자동으로 읽기 위해 load_dotenv를 불러옵니다.
from dotenv import load_dotenv
# OpenAI SDK를 사용하기 위해 OpenAI 클래스를 불러옵니다.
from openai import OpenAI


# 프로젝트 루트의 .env 파일을 환경변수로 로드합니다.
load_dotenv()

# 환경변수에서 OpenAI API 키를 가져옵니다.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
# 환경변수에서 사용할 모델명을 가져오고, 없으면 기본 모델을 사용합니다.
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


# OpenAI API를 사용할 수 있는지 확인하는 함수입니다.
def is_openai_ready() -> bool:
    # API 키가 비어 있지 않으면 True를 반환합니다.
    return bool(OPENAI_API_KEY.strip())


# OpenAI ChatGPT로 자연스러운 답변을 생성하는 함수입니다.
def generate_chat_answer(user_message: str, system_context: str) -> str:
    # API 키가 없으면 로컬 기본 답변을 반환합니다.
    if not is_openai_ready():
        return "OpenAI API 키가 설정되지 않아 로컬 추천 결과로 응답합니다. .env 파일에 OPENAI_API_KEY를 설정하면 자연어 답변이 생성됩니다."
    # OpenAI 클라이언트 객체를 생성합니다.
    client = OpenAI(api_key=OPENAI_API_KEY)
    # Chat Completions API에 전달할 메시지 목록을 구성합니다.
    messages = [
        {
            "role": "system",
            "content": (
                "당신은 커피 주문을 도와주는 친절한 AI 챗봇입니다. "
                "사용자의 취향을 확인하고 메뉴 추천, 주문 확인, 결제 안내를 짧고 자연스럽게 한국어로 답변하세요. "
                "실제 결제는 데모이므로 결제 완료라고 단정하지 말고 결제 페이지 이동 안내로 표현하세요."
            ),
        },
        {
            "role": "user",
            "content": f"사용자 메시지: {user_message}\n\n앱 분석 결과:\n{system_context}",
        },
    ]
    # OpenAI API를 호출하여 응답을 생성합니다.
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=0.6,
        max_tokens=500,
    )
    # 첫 번째 응답 메시지의 내용을 반환합니다.
    return response.choices[0].message.content or "응답을 생성하지 못했습니다."
