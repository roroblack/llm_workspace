# llm 이 대답할 수 있는 질문과 대답할 수 없는 실시간 사내 정보 관련 질문 결과 확인용

# 가장 단순한 LLM 호출 한 번
from google import genai

# 생성 파라미터를 담기 위한 타입 모듈을 불러옵니다.
from google.genai import types

# gemini 모델명과 api key 정보 불러오기
from config import GEMINI_MODEL, GOOGLE_API_KEY, require_env

# Google_API_KEY가 설정되어 있지 않으면 실행을 중단합니다.
if GOOGLE_API_KEY is None:
    raise RuntimeError(
        "GOOGLE_API_KEY 값이 설정되어 있지 않습니다. .env.example을 .env로 복사한 뒤 실제 값을 입력하세요."
    )
api_key = require_env("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

def ask(question: str) -> str:
    """질문을 받아서 LLM에게 전달하고, 답변을 반환합니다."""

    # 질문을 LLM에게 전달하고, 답변을 받습니다.
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=question,
        config=types.GenerateContentConfig(
            max_output_tokens=1024,
            temperature=0.7,
            top_p=0.95,
            stop_sequences=["\n\n"],
        ),
    )

    # LLM의 답변 텍스트를 반환합니다. (응답이 비어 있을 수 있어 빈 문자열로 대체합니다.)
    return (response.text or "").strip()


# LLM이 일반 지식으로 대답할 수 있는 질문들입니다.
ANSWERABLE_QUESTIONS = [
    "파이썬에서 리스트와 튜플의 가장 큰 차이는 무엇인가요?",
    "지구에서 가장 큰 대양의 이름은 무엇인가요?",
]

# LLM이 알 수 없는 실시간 사내 정보 관련 질문들입니다.
UNANSWERABLE_QUESTIONS = [
    "우리 회사 오늘 점심 메뉴는 무엇인가요?",
    "이번 주 우리 팀 회의실 예약 현황을 알려주세요.",
]



def run_demo() -> None:
    """대답 가능한 질문과 불가능한 질문을 차례로 물어보고 결과를 출력합니다."""

    # 먼저 LLM이 대답할 수 있는 일반 질문들을 물어봅니다.
    print("=" * 60)
    print("[1] LLM이 대답할 수 있는 일반 지식 질문")
    print("=" * 60)

    # 일반 질문 목록을 하나씩 순회합니다.
    for question in ANSWERABLE_QUESTIONS:
        # 질문 내용을 먼저 출력합니다.
        print(f"\nQ. {question}")

        # LLM에게 질문을 보내고 답변을 받아 출력합니다.
        print(f"A. {ask(question)}")

    # 다음으로 LLM이 알 수 없는 실시간 사내 정보 질문들을 물어봅니다.
    print("\n" + "=" * 60)
    print("[2] LLM이 대답할 수 없는 실시간 사내 정보 질문")
    print("=" * 60)

    # 사내 정보 질문 목록을 하나씩 순회합니다.
    for question in UNANSWERABLE_QUESTIONS:
        # 질문 내용을 먼저 출력합니다.
        print(f"\nQ. {question}")

        # LLM에게 질문을 보내고 답변을 받아 출력합니다. (모른다고 답하는지 확인합니다.)
        print(f"A. {ask(question)}")


# 이 파일을 직접 실행했을 때만 데모를 수행합니다.
if __name__ == "__main__":
    print(ask("블루투스 이어버드 고를 때 뭘 봐? 3가지 짧게"))
    print(ask("승승장구몰 주문번호 0000123 은 지금 배송 어디까지 왔나요?"))
    # run_demo()
