# -*- coding: utf-8 -*-
"""Gemini API의 Function Calling 자동 실행/수동 실행 예제 모듈입니다."""

# common.py에서 Gemini 클라이언트 생성 함수와 모델명을 가져옵니다.
from common import GEMINI_MODEL, get_genai_client

# google.genai.types는 도구 설정, 자동 호출 비활성화, 대화 기록 구성을 위해 사용합니다.
from google.genai import types

# Function Calling에 연결할 도구 함수를 가져옵니다.
from tools import get_exchange_rate, get_stock

# 모델이 반환한 함수 이름을 실제 파이썬 함수 객체로 연결하는 매핑입니다.
TOOLS = {"get_stock": get_stock, "get_exchange_rate": get_exchange_rate}


def gemini_auto_function_calling() -> None:
    """Gemini SDK의 자동 Function Calling을 실행합니다."""
    # API 키가 설정되어 있지 않으면 common.py의 require_key에서 SystemExit가 발생합니다.
    client = get_genai_client()
    # 도구가 필요한 복합 질문을 준비합니다.
    question = "이어버드 재고 있어? 그리고 가격을 달러로 환산하려면 환율이 얼마야?"
    # Gemini에 함수 도구를 전달하면 SDK가 모델 결정, 함수 실행, 결과 전달을 자동 처리합니다.
    resp = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=question,
        config=types.GenerateContentConfig(
            tools=[get_stock, get_exchange_rate],
            temperature=0,
        ),
    )
    # 최종 응답을 출력합니다.
    print("[Gemini 자동 Function Calling 결과]")
    print(resp.text)


def gemini_manual_function_calling() -> None:
    """Gemini 자동 실행을 끄고 모델의 함수 호출 결정을 직접 관찰합니다."""
    # Gemini 클라이언트를 생성합니다.
    client = get_genai_client()
    # 사용자의 질문을 준비합니다.
    question = "이어버드 재고 알려줘."
    # automatic_function_calling.disable=True로 설정하면 모델은 호출 결정만 만들고 실행하지 않습니다.
    resp = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=question,
        config=types.GenerateContentConfig(
            tools=[get_stock, get_exchange_rate],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            temperature=0,
        ),
    )
    # 함수 호출이 없으면 일반 텍스트 답변을 출력합니다.
    if not resp.function_calls:
        print(resp.text)
        return
    # 최초 사용자 질문을 대화 기록에 저장합니다.
    history = [types.Content(role="user", parts=[types.Part(text=question)])]
    # 모델이 결정한 함수 호출 목록을 순회합니다.
    for fc in resp.function_calls:
        # 모델이 고른 함수 이름과 인자를 출력합니다.
        print(f"모델의 결정 → 함수: {fc.name} | 인자: {dict(fc.args)}")
        # 함수 이름으로 실제 함수를 찾아 실행합니다.
        result = TOOLS[fc.name](**dict(fc.args))
        # 실행 결과를 출력합니다.
        print(f"우리가 실행한 결과: {result}")
        # 모델의 함수 호출 결정을 대화 기록에 추가합니다.
        history.append(types.Content(role="model", parts=[types.Part(function_call=fc)]))
        # 우리가 실행한 함수 결과를 function_response 형태로 대화 기록에 추가합니다.
        history.append(
            types.Content(
                role="user",
                parts=[types.Part.from_function_response(name=fc.name, response={"result": result})],
            )
        )
    # 함수 실행 결과까지 포함한 대화 기록을 다시 모델에 전달해 최종 답변을 생성합니다.
    followup = client.models.generate_content(model=GEMINI_MODEL, contents=history)
    # 최종 답변을 출력합니다.
    print("\n[Gemini 수동 루프 최종 답변]")
    print(followup.text)


def gemini_error_handling_demo() -> None:
    """도구 오류 문자열을 모델에 돌려 자연스러운 안내문을 만드는 예제입니다."""
    # tools 모듈 자체를 import해야 전역 DB_DOWN 값을 바꿀 수 있습니다.
    import tools

    # Gemini 클라이언트를 생성합니다.
    client = get_genai_client()
    # DB 다운 시뮬레이션을 켭니다.
    tools.DB_DOWN = True
    # 장애 상황에서 재고를 묻는 질문을 준비합니다.
    question = "이어버드 재고 확인해 주세요."
    # 자동 실행을 끄고 수동 루프로 오류 문자열을 관찰합니다.
    resp = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=question,
        config=types.GenerateContentConfig(
            tools=[tools.get_stock, tools.get_exchange_rate],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            temperature=0,
        ),
    )
    # 대화 기록을 초기화합니다.
    history = [types.Content(role="user", parts=[types.Part(text=question)])]
    # 모델이 호출하려는 함수가 있으면 직접 실행합니다.
    for fc in resp.function_calls or []:
        # 함수 이름에 맞는 실제 함수 객체를 찾습니다.
        result = {"get_stock": tools.get_stock, "get_exchange_rate": tools.get_exchange_rate}[fc.name](**dict(fc.args))
        # 오류 문자열을 콘솔에 먼저 보여 줍니다.
        print(f"도구 실행 결과: {result}")
        # 모델의 함수 호출 결정을 기록합니다.
        history.append(types.Content(role="model", parts=[types.Part(function_call=fc)]))
        # 도구 결과를 function_response로 기록합니다.
        history.append(types.Content(role="user", parts=[types.Part.from_function_response(name=fc.name, response={"result": result})]))
    # 오류 상황에서도 정중히 안내하도록 시스템 지시를 추가합니다.
    followup = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=history,
        config=types.GenerateContentConfig(
            system_instruction="너는 승승장구몰 CS 상담원이다. 도구 결과가 오류면 사과하고 다음 행동을 안내하라.",
            temperature=0.3,
        ),
    )
    # 최종 안내문을 출력합니다.
    print("\n[Gemini 오류 처리 최종 답변]")
    print(followup.text)
    # 다음 실행에 영향을 주지 않도록 DB_DOWN을 다시 끕니다.
    tools.DB_DOWN = False
