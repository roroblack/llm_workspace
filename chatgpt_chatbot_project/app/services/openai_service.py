# app/services/openai_service.py
# ------------------------------------------------------------
# 이 파일은 OpenAI API 호출 로직을 담당합니다.
# 라우터(main.py)에 모든 코드를 몰아넣지 않고 서비스 파일로 분리하면 유지보수가 쉬워집니다.
#
# [설정 메뉴 지원]
# 프론트엔드 설정 메뉴에서 넘어온 ChatSettings(system_instruction, model,
# temperature, top_p, top_k, max_output_tokens)를 실제 API 호출에 반영합니다.
# gpt-5 / o 계열 모델은 temperature/top_p 커스텀 값을 지원하지 않으므로,
# 해당 파라미터를 자동으로 제외하여 오류를 회피합니다.
# ------------------------------------------------------------

# os 모듈은 환경 변수 값을 읽을 때 사용합니다.
# API 키는 코드에 직접 작성하면 유출 위험이 있으므로 환경 변수로 관리합니다.
import os

# typing 모듈에서 List, Optional 타입을 가져옵니다.
from typing import List, Optional

# dotenv의 load_dotenv 함수를 가져옵니다.
# .env 파일에 저장된 OPENAI_API_KEY 값을 파이썬 환경 변수로 불러오기 위해 사용합니다.
from dotenv import load_dotenv

# OpenAI 공식 파이썬 SDK의 OpenAI 클래스를 가져옵니다.
# 이 클래스를 통해 Chat Completions API를 호출합니다.
from openai import OpenAI

# 앞에서 정의한 데이터 모델을 가져옵니다.
# 대화 기록과 설정 값을 타입 힌트로 사용합니다.
from app.schemas import ChatMessage, ChatSettings

# 프로젝트 루트에 있는 .env 파일을 읽습니다.
# .env 파일이 없어도 오류를 발생시키지 않으므로 개발과 배포 환경 모두에서 사용할 수 있습니다.
load_dotenv()

# 기본 모델명을 환경 변수에서 읽습니다.
# 환경 변수 OPENAI_MODEL이 없으면 gpt-4o-mini를 기본값으로 사용합니다.
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# OpenAI API 키를 환경 변수에서 읽습니다.
# 이 값이 없으면 실제 API 호출 대신 데모 응답을 반환합니다.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# API 키가 있을 때만 OpenAI 클라이언트를 생성합니다.
# 키가 없는데 클라이언트를 무조건 만들면 실행 환경에 따라 오류가 발생할 수 있습니다.
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# 서버 기본 System Instruction 문구입니다.
# 설정 메뉴에서 값을 비워 두면 이 문구가 사용됩니다.
DEFAULT_SYSTEM_INSTRUCTION = (
    "너는 한국어로 친절하고 정확하게 답변하는 FastAPI 기반 ChatGPT 챗봇이다."
)

# 설정 화면의 모델 선택 목록에 표시할 추천 모델 목록입니다.
# 실제 사용 가능한 모델은 계정 권한에 따라 다를 수 있습니다.
AVAILABLE_MODELS = [
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4.1-mini",
    "gpt-4.1",
    "gpt-5-mini",
    "gpt-5",
    "o4-mini",
]

# 추론(reasoning) 모델이 내부 사고에 사용하는 토큰을 위한 최소 여유분입니다.
# gpt-5 / o 계열은 답변을 생성하기 전에 "추론 토큰"을 먼저 소비합니다.
# 사용자가 max_output_tokens를 이 값보다 작게 지정하면 추론 토큰만으로 예산이
# 모두 소진되어 실제 답변(content)이 비어버립니다(finish_reason="length").
# 이를 방지하기 위해 추론 모델에서는 이 값 이상으로 토큰 예산을 자동 상향합니다.
REASONING_MIN_TOKENS = 2000


def is_temperature_restricted_model(model: str) -> bool:
    # gpt-5 계열과 o 계열(o1, o3, o4 ...) 모델은
    # temperature / top_p 커스텀 값을 지원하지 않아 오류가 발생합니다.
    # 모델명을 소문자로 바꿔 접두사로 판별합니다.
    name = (model or "").lower()

    # gpt-5 계열 여부를 확인합니다.
    if name.startswith("gpt-5"):
        return True

    # o1 / o3 / o4 등 추론(reasoning) 계열 여부를 확인합니다.
    # "o" 다음에 숫자가 오는 형태(o1-, o3-, o4-mini 등)를 판별합니다.
    if len(name) >= 2 and name[0] == "o" and name[1].isdigit():
        return True

    return False


def generate_chat_reply(
    message: str,
    history: List[ChatMessage],
    settings: Optional[ChatSettings] = None,
) -> tuple[str, bool, str]:
    # 설정 값이 전달되지 않으면 빈 설정 객체를 사용해 모두 기본값으로 처리합니다.
    if settings is None:
        settings = ChatSettings()

    # 사용할 모델명을 결정합니다.
    # 설정 값이 있으면 우선 사용하고, 없으면 서버 기본 모델을 사용합니다.
    model = settings.model or OPENAI_MODEL

    # System Instruction을 결정합니다.
    # 설정 값이 있으면 우선 사용하고, 없으면 기본 지시문을 사용합니다.
    system_instruction = settings.system_instruction or DEFAULT_SYSTEM_INSTRUCTION

    # API 키가 없으면 실제 ChatGPT API를 호출할 수 없습니다.
    # 수업 또는 화면 테스트가 가능하도록 데모 응답을 반환합니다.
    if client is None:
        # 데모 모드 안내 문장을 생성합니다.
        # 설정 값이 잘 전달되는지 확인할 수 있도록 주요 값을 함께 보여 줍니다.
        demo_reply = (
            "현재 OPENAI_API_KEY가 설정되어 있지 않아 데모 모드로 응답합니다. "
            "실제 ChatGPT 답변을 받으려면 프로젝트 루트의 .env 파일에 "
            "OPENAI_API_KEY 값을 설정하세요.\n\n"
            f"[적용된 설정 미리보기]\n"
            f"- model: {model}\n"
            f"- temperature: {settings.temperature}\n"
            f"- top_p: {settings.top_p}\n"
            f"- top_k: {settings.top_k}\n"
            f"- max_output_tokens: {settings.max_output_tokens}\n"
            f"- system_instruction: {system_instruction}\n\n"
            f"입력한 질문: {message}"
        )

        # 두 번째 값 True는 데모 모드를 사용했다는 의미입니다.
        # 세 번째 값은 실제로 사용하려던 모델명입니다.
        return demo_reply, True, model

    # OpenAI API에 전달할 메시지 목록을 생성합니다.
    # 첫 번째 system 메시지는 챗봇의 역할과 답변 스타일을 지정합니다.
    messages = [{"role": "system", "content": system_instruction}]

    # 클라이언트에서 전달한 이전 대화 내역을 OpenAI API 형식으로 변환합니다.
    for item in history:
        # 허용된 role만 API 메시지에 추가합니다.
        # 잘못된 role이 들어오면 OpenAI API 오류가 발생할 수 있으므로 필터링합니다.
        if item.role in {"user", "assistant", "system"}:
            # Pydantic 모델의 값을 딕셔너리로 변환하여 messages에 추가합니다.
            messages.append({"role": item.role, "content": item.content})

    # 사용자가 방금 입력한 새 질문을 메시지 목록의 마지막에 추가합니다.
    messages.append({"role": "user", "content": message})

    # OpenAI Chat Completions API에 넘길 파라미터를 딕셔너리로 구성합니다.
    # 값이 지정된 파라미터만 골라 담아, 불필요한 기본값 전달을 피합니다.
    params: dict = {
        "model": model,
        "messages": messages,
    }

    # gpt-5 / o 계열 모델은 temperature, top_p 커스텀 값을 지원하지 않습니다.
    # 지원 모델일 때만 해당 파라미터를 추가하여 오류를 자동으로 회피합니다.
    restricted = is_temperature_restricted_model(model)

    # temperature 값이 설정되어 있고, 모델이 지원하는 경우에만 추가합니다.
    if settings.temperature is not None and not restricted:
        params["temperature"] = settings.temperature

    # top_p 값이 설정되어 있고, 모델이 지원하는 경우에만 추가합니다.
    if settings.top_p is not None and not restricted:
        params["top_p"] = settings.top_p

    # max_output_tokens 값이 설정되어 있으면 최대 응답 토큰 수로 지정합니다.
    # gpt-5 / o 계열은 max_completion_tokens, 그 외 모델은 max_tokens 파라미터명을 사용합니다.
    # 파라미터명이 다르면 400 오류가 나므로 모델 계열에 맞춰 자동으로 선택합니다.
    if settings.max_output_tokens is not None:
        if restricted:
            # 추론 모델은 사고 토큰 + 응답 토큰을 함께 소비합니다.
            # 값이 너무 작으면 사고 토큰만으로 소진되어 빈 응답이 나오므로,
            # 최소 여유분(REASONING_MIN_TOKENS) 이상으로 자동 상향합니다.
            params["max_completion_tokens"] = max(
                settings.max_output_tokens, REASONING_MIN_TOKENS
            )
        else:
            params["max_tokens"] = settings.max_output_tokens

    # reasoning_effort(추론 강도)는 gpt-5 / o 계열 추론 모델에만 적용됩니다.
    # 값이 설정되어 있고 모델이 추론 계열일 때만 파라미터로 추가합니다.
    # 일반 모델(gpt-4o 등)에 넣으면 오류가 날 수 있으므로 자동으로 제외합니다.
    if settings.reasoning_effort is not None and restricted:
        params["reasoning_effort"] = settings.reasoning_effort

    # 참고: top_k는 OpenAI Chat Completions API가 직접 지원하지 않습니다.
    # 설정 메뉴에서는 실습용으로 입력받지만 실제 호출 파라미터에는 넣지 않습니다.

    # 구성한 파라미터로 OpenAI Chat Completions API를 호출합니다.
    completion = client.chat.completions.create(**params)

    # 첫 번째 선택지에서 답변 내용과 종료 사유(finish_reason)를 꺼냅니다.
    choice = completion.choices[0]
    reply = choice.message.content
    finish_reason = choice.finish_reason

    # 답변 내용이 비어 있을 때는 원인에 맞는 안내 문구로 대체합니다.
    if not reply:
        if finish_reason == "length":
            # 토큰 예산이 부족해 생성이 중간에 끊긴 경우입니다.
            # 특히 gpt-5 / o 계열은 추론 토큰이 예산을 소진하면 답변이 비어버립니다.
            reply = (
                "답변 토큰이 부족해 응답을 완성하지 못했습니다. "
                "gpt-5 / o 계열은 내부 추론에 토큰을 사용하므로, "
                "설정 메뉴에서 max_output_tokens 값을 더 크게(예: 2000 이상) 지정하거나 "
                "비워 두고 다시 시도해 주세요."
            )
        else:
            # 그 외에 내용이 비어 있는 경우의 기본 안내입니다.
            reply = "응답 내용이 비어 있습니다."

    # 두 번째 값 False는 실제 API를 사용했다는 의미입니다.
    # 세 번째 값은 실제 사용한 모델명입니다.
    return reply, False, model
