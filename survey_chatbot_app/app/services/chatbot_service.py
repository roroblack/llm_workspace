# 앱 설정에서 설문 링크를 가져옵니다.
from app.core.config import SURVEY_LINK

# PyTorch 기반 의도 예측 함수를 가져옵니다.
from app.models.intent_model import predict_intent

# 설문 상태 관리 함수를 가져옵니다.
from app.services.survey_service import (
    build_summary,
    get_current_question,
    get_session,
    load_questions,
    save_answer,
    start_session,
)

# OpenAI 답변 생성 함수를 가져옵니다.
from app.services.openai_service import generate_openai_reply

# 선택지가 있는 질문을 보기 좋게 출력하는 함수입니다.
def format_question(question: dict) -> str:
    # 질문이 없으면 완료 문장을 반환합니다.
    if question is None:
        # 설문 완료 안내입니다.
        return "설문이 모두 완료되었습니다. '요약'이라고 입력하면 응답 내용을 확인할 수 있습니다."

    # 기본 질문 문장을 만듭니다.
    text = f"Q{question['id']}. {question['question']}"

    # 선택지가 있는 경우 선택지를 함께 표시합니다.
    if question.get("options"):
        # 선택지 목록을 쉼표로 연결합니다.
        options = ", ".join(question["options"])

        # 질문 아래에 선택지를 추가합니다.
        text += f"\n선택지: {options}"

    # 완성된 질문 문자열을 반환합니다.
    return text

# 사용자의 메시지를 처리하는 메인 함수입니다.
def handle_chat(message: str, session_id: str) -> dict:
    # PyTorch 모델로 사용자 의도를 예측합니다.
    intent_result = predict_intent(message)

    # 예측된 의도명을 가져옵니다.
    intent = str(intent_result["intent"])

    # 의도 예측 신뢰도를 가져옵니다.
    confidence = float(intent_result["confidence"])

    # 전체 설문 문항 수를 계산합니다.
    total_steps = len(load_questions())

    # 사용자가 설문 시작을 요청한 경우입니다.
    if intent == "start":
        # 세션을 새로 초기화합니다.
        start_session(session_id)

        # 첫 번째 질문을 가져옵니다.
        question = get_current_question(session_id)

        # 챗봇 기본 문맥을 구성합니다.
        bot_context = "설문을 시작합니다.\n" + format_question(question)

    # 사용자가 설문 링크를 요청한 경우입니다.
    elif intent == "link":
        # 구글 설문 링크 안내 문맥을 구성합니다.
        bot_context = f"구글 설문지로 바로 이동하려면 아래 링크를 사용하세요.\n{SURVEY_LINK}"

    # 사용자가 요약을 요청한 경우입니다.
    elif intent == "summary":
        # 현재까지 저장된 응답 요약을 생성합니다.
        bot_context = build_summary(session_id)

    # 사용자가 도움말을 요청한 경우입니다.
    elif intent == "help":
        # 사용법 안내 문맥을 구성합니다.
        bot_context = (
            "사용 방법입니다.\n"
            "1. '설문 시작'이라고 입력합니다.\n"
            "2. 질문에 차례대로 답변합니다.\n"
            "3. '요약'이라고 입력하면 응답 결과를 확인합니다.\n"
            "4. '링크'라고 입력하면 구글 설문 링크를 확인합니다."
        )

    # 그 외 입력은 설문 답변으로 처리합니다.
    else:
        # 현재 질문을 확인합니다.
        current_question = get_current_question(session_id)

        # 현재 질문이 없으면 완료 상태로 처리합니다.
        if current_question is None:
            # 완료 후 안내 문맥을 구성합니다.
            bot_context = "이미 모든 문항에 응답했습니다.\n" + build_summary(session_id)
        else:
            # 사용자의 입력을 현재 질문의 답변으로 저장합니다.
            save_answer(session_id, message)

            # 다음 질문을 가져옵니다.
            next_question = get_current_question(session_id)

            # 다음 질문이 있으면 다음 질문을 안내합니다.
            if next_question is not None:
                # 다음 질문 안내 문맥을 구성합니다.
                bot_context = "응답이 저장되었습니다.\n" + format_question(next_question)
            else:
                # 모든 질문 완료 문맥을 구성합니다.
                bot_context = "설문 응답이 모두 저장되었습니다. 감사합니다.\n" + build_summary(session_id)

    # OpenAI를 사용하여 자연스러운 챗봇 응답을 생성합니다.
    reply = generate_openai_reply(message, intent, bot_context)

    # 최신 세션 상태를 가져옵니다.
    session = get_session(session_id)

    # API 응답 딕셔너리를 반환합니다.
    return {
        "reply": reply,
        "intent": intent,
        "confidence": confidence,
        "step": int(session["step"]),
        "total_steps": total_steps,
    }
