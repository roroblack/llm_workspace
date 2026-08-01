# Google Gemini 공식 Gen AI SDK 클라이언트를 가져옵니다.
from google import genai

# Gemini 생성 설정 타입을 사용하기 위해 types 모듈을 가져옵니다.
from google.genai import types

# 앱 설정값을 가져옵니다.
from app.core.config import settings

# 기능별 프롬프트 생성 함수를 가져옵니다.
from app.services.prompt_factory import build_prompt


# Gemini API 호출을 담당하는 서비스 클래스입니다.
class GeminiService:
    # 서비스 객체가 생성될 때 Gemini 클라이언트를 준비합니다.
    def __init__(self):
        # API Key가 없으면 명확한 오류 메시지를 발생시킵니다.
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하십시오.")

        # Gemini Developer API용 클라이언트를 생성합니다.
        self.client = genai.Client(api_key=settings.gemini_api_key)

    # Gemini generate_content API를 사용하여 텍스트를 생성합니다.
    def generate(
        self,
        prompt: str,
        task_type: str,
        system_instruction: str,
        model: str | None,
        temperature: float,
        top_p: float,
        max_output_tokens: int,
    ) -> tuple[str, str]:
        # 요청별 모델명이 있으면 사용하고, 없으면 .env 기본 모델을 사용합니다.
        selected_model = model or settings.gemini_model

        # 기능 유형에 맞는 최종 프롬프트를 생성합니다.
        final_prompt = build_prompt(task_type, prompt)

        # Gemini 생성 옵션을 구성합니다.
        config = types.GenerateContentConfig(
            # 시스템 지시문으로 모델의 역할과 응답 방식을 지정합니다.
            system_instruction=system_instruction,
            # 출력의 창의성과 무작위성을 조절합니다.
            temperature=temperature,
            # 누적 확률 기반 샘플링 범위를 조절합니다.
            top_p=top_p,
            # 최대 출력 길이를 제한합니다.
            max_output_tokens=max_output_tokens,
        )

        # Gemini API에 프롬프트와 설정을 전달하여 결과를 생성합니다.
        response = self.client.models.generate_content(
            # 사용할 Gemini 모델명을 지정합니다.
            model=selected_model,
            # 사용자 요청 프롬프트를 전달합니다.
            contents=final_prompt,
            # 앞에서 구성한 생성 설정을 전달합니다.
            config=config,
        )

        # Gemini 응답 텍스트와 실제 사용 모델명을 반환합니다.
        return response.text or "", selected_model
