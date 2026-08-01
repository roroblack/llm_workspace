# JSON 파일을 읽고 쓰기 위해 json 모듈을 불러옵니다.
import json

# 경로 처리를 위해 Path를 불러옵니다.
from pathlib import Path

# 타입 힌트를 위해 Any와 Dict와 List를 불러옵니다.
from typing import Any, Dict, List

# 설문 문항 파일 경로입니다.
QUESTION_PATH = Path(__file__).resolve().parent.parent / "data" / "survey_questions.json"

# 세션별 설문 응답을 메모리에 저장하는 딕셔너리입니다.
SESSIONS: Dict[str, Dict[str, Any]] = {}

# 설문 문항 목록을 읽는 함수입니다.
def load_questions() -> List[Dict[str, Any]]:
    # UTF-8 인코딩으로 JSON 파일을 엽니다.
    with QUESTION_PATH.open("r", encoding="utf-8") as file:
        # JSON 데이터를 파이썬 리스트로 변환합니다.
        return json.load(file)

# 새 설문 세션을 시작하는 함수입니다.
def start_session(session_id: str) -> Dict[str, Any]:
    # 해당 세션의 진행 단계와 답변 저장소를 초기화합니다.
    SESSIONS[session_id] = {"step": 0, "answers": {}}

    # 초기화된 세션 상태를 반환합니다.
    return SESSIONS[session_id]

# 세션 상태를 가져오는 함수입니다.
def get_session(session_id: str) -> Dict[str, Any]:
    # 세션이 없으면 새 세션을 생성합니다.
    if session_id not in SESSIONS:
        # 새 설문 세션을 시작합니다.
        return start_session(session_id)

    # 기존 세션 상태를 반환합니다.
    return SESSIONS[session_id]

# 현재 질문을 반환하는 함수입니다.
def get_current_question(session_id: str) -> Dict[str, Any] | None:
    # 설문 문항 목록을 불러옵니다.
    questions = load_questions()

    # 현재 세션 상태를 가져옵니다.
    session = get_session(session_id)

    # 현재 진행 단계를 가져옵니다.
    step = session["step"]

    # 모든 문항에 응답했다면 None을 반환합니다.
    if step >= len(questions):
        return None

    # 현재 단계의 질문을 반환합니다.
    return questions[step]

# 사용자의 답변을 저장하는 함수입니다.
def save_answer(session_id: str, answer: str) -> Dict[str, Any]:
    # 설문 문항 목록을 불러옵니다.
    questions = load_questions()

    # 현재 세션 상태를 가져옵니다.
    session = get_session(session_id)

    # 현재 진행 단계를 가져옵니다.
    step = session["step"]

    # 모든 문항이 완료된 경우 현재 상태를 그대로 반환합니다.
    if step >= len(questions):
        return session

    # 현재 질문 정보를 가져옵니다.
    question = questions[step]

    # 질문 key를 기준으로 사용자의 답변을 저장합니다.
    session["answers"][question["key"]] = answer

    # 다음 질문으로 이동하기 위해 단계를 1 증가시킵니다.
    session["step"] = step + 1

    # 갱신된 세션 상태를 반환합니다.
    return session

# 설문 답변 요약 문자열을 만드는 함수입니다.
def build_summary(session_id: str) -> str:
    # 설문 문항 목록을 불러옵니다.
    questions = load_questions()

    # 현재 세션 상태를 가져옵니다.
    session = get_session(session_id)

    # 요약 문장들을 저장할 리스트입니다.
    lines = ["📊 설문 응답 요약"]

    # 문항 순서대로 답변을 정리합니다.
    for question in questions:
        # 질문 key를 가져옵니다.
        key = question["key"]

        # 저장된 답변이 없으면 미응답으로 표시합니다.
        answer = session["answers"].get(key, "미응답")

        # 질문과 답변을 한 줄로 추가합니다.
        lines.append(f"- {question['question']}\n  → {answer}")

    # 줄바꿈으로 합쳐 최종 요약 문자열을 반환합니다.
    return "\n".join(lines)
