# -*- coding: utf-8 -*-
"""
gemini_agent_loop.py

Google Gemini API의 function calling을 수동 루프로 실행하는 예제입니다.
"""

# Google GenAI SDK의 types를 가져옵니다.
from google.genai import types

# common.py에서 Gemini 클라이언트 생성 함수와 모델명을 가져옵니다.
from common import get_genai_client, GEMINI_MODEL

# 실습 도구 함수와 함수 매핑을 가져옵니다.
from data_tools import get_stock, get_reorder_level, TOOLS


def trim_history(history: list, keep: int = 4) -> list:
    """첫 사용자 질문은 보존하고 최근 keep개 메시지만 유지합니다."""
    # history 길이가 보존 기준보다 짧으면 그대로 반환합니다.
    if len(history) <= keep + 1:
        # 자를 필요가 없는 대화 기록입니다.
        return history
    # 첫 메시지는 원래 목표이므로 반드시 보존합니다.
    head = history[:1]
    # 최근 keep개 메시지만 유지합니다.
    tail = history[-keep:]
    # 첫 메시지와 최근 메시지를 합쳐 반환합니다.
    return head + tail


def run_gemini_agent(question: str, max_steps: int = 6) -> str | None:
    """Gemini API로 ReAct 방식의 수동 Agent Loop를 실행합니다."""
    # .env의 GOOGLE_API_KEY를 사용해 Gemini 클라이언트를 생성합니다.
    client = get_genai_client()
    # 도구 목록과 시스템 지시를 포함한 설정을 만듭니다.
    config = types.GenerateContentConfig(
        # Gemini에게 사용할 수 있는 도구 함수를 알려줍니다.
        tools=[get_stock, get_reorder_level],
        # 자동 실행을 끄고 모델의 결정만 받은 뒤 우리가 직접 실행합니다.
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        # 에이전트 역할과 판단 기준을 시스템 지시로 제공합니다.
        system_instruction=(
            "너는 승승장구몰 재고 관리 에이전트다. "
            "도구로 재고와 재주문 기준을 확인하고, "
            "재고가 재주문 기준 이하이면 재주문을 권유하라. 한국어로 답하라."
        ),
        # 도구 선택의 일관성을 위해 temperature를 0으로 둡니다.
        temperature=0,
    )
    # 대화 기록은 첫 사용자 질문에서 시작합니다.
    history = [types.Content(role="user", parts=[types.Part(text=question)])]
    # 반복 호출 방지를 위해 이미 실행한 도구명+인자 조합을 저장합니다.
    seen_calls = set()
    # 최대 max_steps까지만 반복합니다.
    for step in range(1, max_steps + 1):
        # 현재 history 전체를 모델에 전달합니다.
        resp = client.models.generate_content(model=GEMINI_MODEL, contents=history, config=config)
        # usage_metadata가 있으면 토큰 사용량을 출력합니다.
        if getattr(resp, "usage_metadata", None):
            # 토큰 사용량 객체를 변수에 저장합니다.
            usage = resp.usage_metadata
            # 입력/출력/전체 토큰 수를 안전하게 가져옵니다.
            prompt_tokens = getattr(usage, "prompt_token_count", "?")
            # 후보 출력 토큰 수를 안전하게 가져옵니다.
            output_tokens = getattr(usage, "candidates_token_count", "?")
            # 총 토큰 수를 안전하게 가져옵니다.
            total_tokens = getattr(usage, "total_token_count", "?")
            # 현재 스텝의 토큰 정보를 출력합니다.
            print(f"[STEP {step}] history {len(history)}개 | 입력 {prompt_tokens} + 출력 {output_tokens} = 총 {total_tokens} 토큰")
        # 모델이 더 이상 도구 호출을 요청하지 않으면 최종 답변으로 종료합니다.
        if not resp.function_calls:
            # 최종 답변 단계임을 출력합니다.
            print(f"[STEP {step}] 최종 답변")
            # 최종 답변을 출력합니다.
            print(resp.text)
            # 최종 답변을 반환합니다.
            return resp.text
        # 모델의 도구 호출 결정을 history에 기록합니다.
        history.append(resp.candidates[0].content)
        # 모델이 요청한 각 함수 호출을 순회합니다.
        for fc in resp.function_calls:
            # 함수 호출 인자를 일반 dict로 변환합니다.
            args = dict(fc.args)
            # 도구명과 정렬된 인자 튜플로 중복 감지용 서명을 만듭니다.
            signature = (fc.name, tuple(sorted(args.items())))
            # 이미 실행한 호출이면 무한 반복 가능성이 있으므로 중단합니다.
            if signature in seen_calls:
                # 중복 호출 경고를 출력합니다.
                print("[경고] 동일한 도구·인자 반복 호출 감지 → 강제 종료")
                # 안전 종료합니다.
                return None
            # 처음 보는 호출이면 기록합니다.
            seen_calls.add(signature)
            # 모델이 선택한 도구 이름과 인자를 출력합니다.
            print(f"[STEP {step}] 호출: {fc.name} {args}")
            # 도구 이름으로 실제 함수를 찾아 실행합니다.
            result = TOOLS[fc.name](**args)
            # 실행 결과를 출력합니다.
            print("           관찰:", result)
            # 실행 결과를 function_response 형식으로 history에 되돌립니다.
            history.append(types.Content(role="user", parts=[
                types.Part.from_function_response(name=fc.name, response={"result": result})
            ]))
        # history가 너무 길어지면 첫 질문과 최근 메시지만 남깁니다.
        history = trim_history(history, keep=4)
    # 최대 스텝에 도달하면 안전장치 메시지를 출력합니다.
    print("[종료] 최대 스텝 도달 — 안전장치 작동")
    # 최종 답변이 없음을 의미합니다.
    return None


def run_gemini_agent_demo() -> None:
    """Gemini Agent Loop 데모를 실행합니다."""
    # API 키가 없거나 호출이 실패해도 프로그램 전체가 죽지 않도록 예외 처리합니다.
    try:
        # 대표 질문을 실행합니다.
        run_gemini_agent("스마트워치 재고를 확인하고, 재주문이 필요하면 알려줘.")
    # SystemExit은 common.require_key가 키 누락 시 발생시킵니다.
    except SystemExit as e:
        # 키 설정 안내를 출력합니다.
        print(e)
    # 그 밖의 API 오류도 사용자에게 표시합니다.
    except Exception as e:
        # 예외 내용을 출력합니다.
        print("Gemini 실행 오류:", e)
