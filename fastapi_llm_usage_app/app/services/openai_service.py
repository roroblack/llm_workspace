# OpenAI 공식 Python SDK에서 OpenAI 클라이언트를 가져옵니다.
from openai import OpenAI

# 앱 설정값을 가져옵니다.
from app.core.config import settings

# 기능별 프롬프트 생성 함수를 가져옵니다.
from app.services.prompt_factory import build_prompt


# OpenAI API 호출을 담당하는 서비스 클래스입니다.
class OpenAIService:
    # 서비스 객체가 생성될 때 API 클라이언트를 준비합니다.
    def __init__(self):
        # API Key가 없으면 명확한 오류 메시지를 발생시킵니다.
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하십시오.")

        # OpenAI 클라이언트를 생성합니다.
        self.client = OpenAI(api_key=settings.openai_api_key, timeout=settings.default_timeout_seconds)

    # OpenAI Responses API를 사용하여 텍스트를 생성합니다.
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
        selected_model = model or settings.openai_model

        # 기능 유형에 맞는 최종 프롬프트를 생성합니다.
        final_prompt = build_prompt(task_type, prompt)

        # OpenAI Responses API를 호출합니다.
        response = self.client.responses.create(
            # 사용할 OpenAI 모델명을 지정합니다.
            model=selected_model,
            # 시스템 지시문으로 모델의 응답 태도와 역할을 지정합니다.
            instructions=system_instruction,
            # 실제 사용자 요청 프롬프트를 전달합니다.
            input=final_prompt,
            # 출력의 창의성과 무작위성을 조절합니다.
            temperature=temperature,
            # 누적 확률 기반 샘플링 범위를 조절합니다.
            top_p=top_p,
            # 최대 출력 길이를 제한합니다.
            max_output_tokens=max_output_tokens,
        )

        # 생성된 텍스트와 실제 사용 모델명을 반환합니다.
        return response.output_text, selected_model
