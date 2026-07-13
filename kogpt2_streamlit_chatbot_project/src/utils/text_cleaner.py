"""
KoGPT2 생성 결과를 화면에 보기 좋게 정리하는 유틸리티 파일입니다.

언어 모델은 토큰 단위로 문장을 생성하므로 특수 토큰, 제어 문자, 반복 공백 등이
섞일 수 있습니다. Streamlit 화면에 표시하기 전에 정리하면 결과가 더 읽기 좋아집니다.
"""

# 정규표현식 처리를 위한 파이썬 기본 라이브러리입니다.
# 제어 문자 제거, 반복 공백 축소 같은 문자열 정리에 사용합니다.
import re


PROMPT_LEAK_MARKERS = (
    "다음은 사용자와",
    "한국어 인공지능 챗봇",
    "사용자:",
    "챗봇:",
    "질문:",
    "답변:",
)

LOW_QUALITY_MARKERS = (
    "#withoutnote",
    "#functional",
    "#lifelyture",
    "#songpanet",
    "#mindbox",
    "</d>",
    "<d>",
    "MBC",
    "KBS",
    "방송된",
    "스페셜 MC",
    "아까 말했던",
    "단어장면",
    "extended",
)


# 생성된 문자열을 정리하는 함수를 정의합니다.
# text 매개변수에는 tokenizer.decode()로 복원된 문자열이 들어옵니다.
def clean_generated_text(text: str) -> str:
    # 유니코드 replacement character(�)는 디코딩 오류가 있을 때 나타날 수 있으므로 제거합니다.
    text = text.replace("�", "")

    # ASCII 제어 문자를 공백으로 바꿉니다.
    # 줄바꿈, 탭, 보이지 않는 문자가 섞이면 채팅 출력이 지저분해질 수 있습니다.
    text = re.sub(r"[\x00-\x1F\x7F]", " ", text)

    # KoGPT2에서 출력될 수 있는 문장 시작/종료 특수 토큰을 제거합니다.
    # 사용자가 읽는 답변에는 특수 토큰이 보이지 않는 것이 좋습니다.
    text = text.replace("</s>", " ")
    text = text.replace("</d>", " ")
    text = text.replace("<d>", " ")

    # 패딩 토큰 문자열을 제거합니다.
    # 패딩 토큰은 문장 길이를 맞추기 위한 기호이므로 최종 답변에는 필요하지 않습니다.
    text = text.replace("<pad>", " ")

    # 알 수 없는 토큰 문자열을 제거합니다.
    # 알 수 없는 토큰이 화면에 그대로 보이면 문장이 어색해 보일 수 있습니다.
    text = text.replace("<unk>", " ")

    # 마스크 토큰 문자열을 제거합니다.
    # GPT 생성에서는 주로 사용하지 않지만 출력될 경우를 대비합니다.
    text = text.replace("<mask>", " ")

    # 웹 말뭉치에서 섞여 나오기 쉬운 해시태그와 HTML 비슷한 태그를 걷어냅니다.
    text = re.sub(r"#\S*", " ", text)
    text = re.sub(r"</?[^>\s]{1,30}>", " ", text)

    # 여러 개의 공백을 하나의 공백으로 줄입니다.
    # 토큰 디코딩 후 공백이 반복될 수 있으므로 보기 좋게 정리합니다.
    text = re.sub(r"\s+", " ", text)

    # 문장 앞뒤의 불필요한 공백을 제거합니다.
    # 최종 화면 출력이 깔끔해집니다.
    text = text.strip()

    # 정리된 문자열을 반환합니다.
    return text


# 챗봇 프롬프트를 구성하는 함수를 정의합니다.
# KoGPT2는 대화 전용으로 미세조정된 모델이 아니므로 역할 표시를 넣어 답변 방향을 잡습니다.
def build_chat_prompt(user_message: str, history: list[dict[str, str]] | None = None) -> str:
    # 대화 이력이 None이면 빈 리스트로 바꿉니다.
    # 이렇게 하면 이후 반복문에서 NoneType 오류가 발생하지 않습니다.
    history = history or []

    # 프롬프트에 들어갈 문자열 조각을 저장할 리스트를 만듭니다.
    # 여러 줄을 리스트에 담은 뒤 join하면 구조적인 프롬프트를 만들기 쉽습니다.
    prompt_parts: list[str] = []

    # 최근 대화 이력만 프롬프트에 넣기 위해 마지막 2개 메시지를 사용합니다.
    # 너무 긴 이력을 넣으면 입력 토큰이 길어져 속도가 느려지고 답변 품질이 흔들릴 수 있습니다.
    recent_history = history[-2:]

    # 최근 대화 이력을 순서대로 프롬프트에 추가합니다.
    # role 값이 user이면 사용자 발화, assistant이면 챗봇 응답으로 표시합니다.
    for message in recent_history:
        # 현재 메시지의 역할 값을 가져옵니다.
        # 값이 없으면 빈 문자열을 사용하여 KeyError를 방지합니다.
        role = message.get("role", "")

        # 현재 메시지의 내용을 가져옵니다.
        # 값이 없으면 빈 문자열을 사용하여 KeyError를 방지합니다.
        content = message.get("content", "")

        # 사용자 메시지이면 "사용자:" 형식으로 추가합니다.
        # 이 형식은 모델이 대화 흐름을 구분하는 데 도움을 줍니다.
        if role == "user":
            prompt_parts.append(f"사용자: {content}")

        # 챗봇 메시지이면 "챗봇:" 형식으로 추가합니다.
        # 이전 답변을 함께 넣으면 짧은 문맥 유지에 도움이 됩니다.
        elif role == "assistant":
            prompt_parts.append(f"챗봇: {content}")

    # 현재 사용자의 새 입력을 프롬프트에 추가합니다.
    # 모델은 이 문장 뒤의 챗봇 답변을 생성하게 됩니다.
    prompt_parts.append(f"사용자: {user_message}")

    # 모델이 이어서 생성할 위치를 "챗봇:"으로 시작시킵니다.
    # 이렇게 하면 답변 형식이 비교적 일정하게 유지됩니다.
    prompt_parts.append("챗봇:")

    # 줄바꿈으로 프롬프트 조각을 연결합니다.
    # 대화 구조가 잘 보이도록 각 발화를 한 줄로 분리합니다.
    prompt = "\n".join(prompt_parts)

    # 완성된 프롬프트를 반환합니다.
    return prompt


# 모델 출력에서 챗봇 답변 부분만 잘라내는 함수를 정의합니다.
# 전체 디코딩 결과에는 입력 프롬프트까지 포함될 수 있으므로 후처리가 필요합니다.
def extract_answer(full_text: str, prompt: str) -> str:
    # 전체 생성 결과가 입력 프롬프트로 시작하면 프롬프트 부분을 제거합니다.
    # 이렇게 해야 사용자가 입력한 문장이 답변에 반복 표시되지 않습니다.
    if prompt and full_text.startswith(prompt):
        full_text = full_text[len(prompt):]

    # 프롬프트나 다음 턴 라벨이 새어 나오면 그 앞까지만 답변으로 사용합니다.
    for marker in PROMPT_LEAK_MARKERS:
        if marker in full_text:
            full_text = full_text.split(marker)[0]

    # 혹시 남아 있는 "사용자:" 이후 문장은 다음 턴처럼 보일 수 있으므로 제거합니다.
    # 생성 모델이 대화 형식을 흉내 내며 새 사용자 발화를 만들어 내는 것을 막기 위한 후처리입니다.
    full_text = full_text.split("사용자:")[0]

    # 혹시 남아 있는 "챗봇:" 라벨을 제거합니다.
    # 화면에는 실제 답변 문장만 표시하는 것이 자연스럽습니다.
    full_text = full_text.replace("챗봇:", " ")

    # 공통 정리 함수를 적용하여 특수 토큰과 불필요한 공백을 제거합니다.
    answer = clean_generated_text(full_text)

    answer = trim_answer(answer)

    # 답변이 비어 있으면 기본 안내 답변을 사용합니다.
    # 모델이 종료 토큰만 생성하거나 너무 짧게 끝나는 경우를 대비합니다.
    if not answer:
        answer = "답변을 생성하지 못했습니다. 질문을 조금 더 구체적으로 입력해 주세요."

    # 최종 답변을 반환합니다.
    return answer


def get_rule_based_reply(user_message: str) -> str | None:
    text = user_message.strip()
    lowered = text.lower()
    compact = re.sub(r"\s+", "", lowered)

    if compact in {"hi", "hello", "hey", "하이"}:
        return "안녕하세요! 무엇을 도와드릴까요?"

    if "안녕" in compact and len(compact) <= 20:
        return "안녕하세요! 반가워요. 편하게 말 걸어 주세요."

    if "뭐하는" in compact or "뭐하" in compact:
        return "지금은 사용자가 입력한 문장을 바탕으로 한국어 답변을 생성하고 있어요."

    if "기분" in compact:
        return "저는 실제 감정은 없지만, 지금은 잘 작동하고 있어요. 물어봐 줘서 고마워요."

    if "고마" in compact or "감사" in compact:
        return "천만에요. 또 궁금한 게 있으면 편하게 물어봐 주세요."

    if "누구" in compact or "이름" in compact:
        return "저는 KoGPT2 기반 한국어 챗봇입니다."

    if "파이썬" in compact and ("뭐" in compact or "무엇" in compact):
        return "파이썬은 문법이 비교적 쉬운 프로그래밍 언어입니다. 웹 개발, 데이터 분석, 인공지능 같은 분야에서 많이 사용돼요."

    if "점심" in compact and ("추천" in compact or "메뉴" in compact):
        return "점심으로는 비빔밥, 김치찌개, 제육볶음, 샐러드, 돈가스 중에서 골라보면 좋아요."

    if "날씨" in compact:
        return "이 앱은 실시간 날씨를 조회하지는 못해요. 날씨 앱이나 웹 검색으로 현재 지역 날씨를 확인해 주세요."

    if "추천" in compact:
        return "추천을 도와드릴게요. 원하는 분야나 조건을 조금 더 구체적으로 알려 주세요."

    if "문장" in compact and ("만들" in compact or "생성" in compact):
        return "오늘은 작은 시도 하나가 생각보다 큰 변화를 만들 수 있는 날입니다."

    return None


def fallback_answer(user_message: str) -> str:
    rule_reply = get_rule_based_reply(user_message)
    if rule_reply:
        return rule_reply

    return "질문을 잘 이해하지 못했어요. 한 문장으로 조금 더 구체적으로 말해 주세요."


def trim_answer(answer: str, max_chars: int = 180) -> str:
    answer = answer.strip()
    if len(answer) <= max_chars:
        return answer

    shortened = answer[:max_chars]
    sentence_end = max(shortened.rfind("."), shortened.rfind("?"), shortened.rfind("!"), shortened.rfind("요"))
    if sentence_end >= 20:
        return shortened[: sentence_end + 1].strip()
    return shortened.rstrip() + "..."


def is_low_quality_answer(answer: str, user_message: str) -> bool:
    answer = answer.strip()
    if len(answer) < 2:
        return True

    if any(marker in answer for marker in PROMPT_LEAK_MARKERS):
        return True

    lowered_answer = answer.lower()
    if any(marker.lower() in lowered_answer for marker in LOW_QUALITY_MARKERS):
        return True

    if "#" in answer or re.search(r"</?[a-zA-Z][^>]*>", answer):
        return True

    if re.search(r"20\d{2}년\s*\d{1,2}월|\d{4}년\s*\d{1,2}월", answer):
        return True

    hangul_in_user = len(re.findall(r"[가-힣]", user_message))
    ascii_in_answer = len(re.findall(r"[A-Za-z]", answer))
    hangul_in_answer = len(re.findall(r"[가-힣]", answer))
    if hangul_in_user and ascii_in_answer > max(10, hangul_in_answer):
        return True

    if hangul_in_user and re.search(r"[A-Za-z]{4,}", answer):
        return True

    if answer.startswith(("(", "[", "{")):
        return True

    last_word = answer.rstrip(".!?요").split(" ")[-1]
    if len(answer) > 20 and last_word in {"그", "이", "가", "은", "는", "을", "를", "의", "과", "와"}:
        return True

    return False
