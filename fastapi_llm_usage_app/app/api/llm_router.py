# FastAPI 라우터와 HTTP 예외 처리를 사용하기 위해 가져옵니다.
from fastapi import APIRouter, HTTPException

# 요청과 응답 데이터 모델을 가져옵니다.
from app.schemas.llm_schema import LLMRequest, LLMResponse

# OpenAI API 호출 서비스 클래스를 가져옵니다.
from app.services.openai_service import OpenAIService

# Gemini API 호출 서비스 클래스를 가져옵니다.
from app.services.gemini_service import GeminiService

# /api/llm 하위 URL을 담당하는 라우터를 생성합니다.
router = APIRouter(prefix="/api/llm", tags=["LLM"])


# OpenAI API를 사용하는 공통 실행 엔드포인트입니다.
@router.post("/openai", response_model=LLMResponse)
def run_openai(request: LLMRequest):
    # API 호출 중 오류가 발생할 수 있으므로 예외 처리를 적용합니다.
    try:
        # OpenAI 서비스 객체를 생성합니다.
        service = OpenAIService()

        # 요청값과 config 값을 함께 전달하여 OpenAI API를 호출합니다.
        result, model = service.generate(
            prompt=request.prompt,
            task_type=request.task_type,
            system_instruction=request.system_instruction,
            model=request.model,
            temperature=request.temperature,
            top_p=request.top_p,
            max_output_tokens=request.max_output_tokens,
        )

        # FastAPI 응답 모델에 맞추어 결과를 반환합니다.
        return LLMResponse(provider="openai", model=model, task_type=request.task_type, result=result)

    # 모든 예외를 HTTP 500 응답으로 변환하여 클라이언트에 전달합니다.
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Gemini API를 사용하는 공통 실행 엔드포인트입니다.
@router.post("/gemini", response_model=LLMResponse)
def run_gemini(request: LLMRequest):
    # API 호출 중 오류가 발생할 수 있으므로 예외 처리를 적용합니다.
    try:
        # Gemini 서비스 객체를 생성합니다.
        service = GeminiService()

        # 요청값과 config 값을 함께 전달하여 Gemini API를 호출합니다.
        result, model = service.generate(
            prompt=request.prompt,
            task_type=request.task_type,
            system_instruction=request.system_instruction,
            model=request.model,
            temperature=request.temperature,
            top_p=request.top_p,
            max_output_tokens=request.max_output_tokens,
        )

        # FastAPI 응답 모델에 맞추어 결과를 반환합니다.
        return LLMResponse(provider="gemini", model=model, task_type=request.task_type, result=result)

    # 모든 예외를 HTTP 500 응답으로 변환하여 클라이언트에 전달합니다.
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 문장 생성 전용 OpenAI 엔드포인트입니다.
@router.post("/openai/sentence", response_model=LLMResponse)
def openai_sentence(request: LLMRequest):
    # 요청의 기능 유형을 문장 생성으로 고정합니다.
    request.task_type = "sentence"
    # 공통 OpenAI 실행 함수를 재사용합니다.
    return run_openai(request)


# 질의응답 전용 OpenAI 엔드포인트입니다.
@router.post("/openai/qa", response_model=LLMResponse)
def openai_qa(request: LLMRequest):
    # 요청의 기능 유형을 질의응답으로 고정합니다.
    request.task_type = "qa"
    # 공통 OpenAI 실행 함수를 재사용합니다.
    return run_openai(request)


# 요약 전용 OpenAI 엔드포인트입니다.
@router.post("/openai/summary", response_model=LLMResponse)
def openai_summary(request: LLMRequest):
    # 요청의 기능 유형을 요약으로 고정합니다.
    request.task_type = "summary"
    # 공통 OpenAI 실행 함수를 재사용합니다.
    return run_openai(request)


# 번역 전용 OpenAI 엔드포인트입니다.
@router.post("/openai/translation", response_model=LLMResponse)
def openai_translation(request: LLMRequest):
    # 요청의 기능 유형을 번역으로 고정합니다.
    request.task_type = "translation"
    # 공통 OpenAI 실행 함수를 재사용합니다.
    return run_openai(request)


# 채팅 전용 OpenAI 엔드포인트입니다.
@router.post("/openai/chat", response_model=LLMResponse)
def openai_chat(request: LLMRequest):
    # 요청의 기능 유형을 채팅으로 고정합니다.
    request.task_type = "chat"
    # 공통 OpenAI 실행 함수를 재사용합니다.
    return run_openai(request)


# 다양한 Use Case 전용 OpenAI 엔드포인트입니다.
@router.post("/openai/usecase", response_model=LLMResponse)
def openai_usecase(request: LLMRequest):
    # 요청의 기능 유형을 Use Case로 고정합니다.
    request.task_type = "usecase"
    # 공통 OpenAI 실행 함수를 재사용합니다.
    return run_openai(request)


# 문장 생성 전용 Gemini 엔드포인트입니다.
@router.post("/gemini/sentence", response_model=LLMResponse)
def gemini_sentence(request: LLMRequest):
    # 요청의 기능 유형을 문장 생성으로 고정합니다.
    request.task_type = "sentence"
    # 공통 Gemini 실행 함수를 재사용합니다.
    return run_gemini(request)


# 질의응답 전용 Gemini 엔드포인트입니다.
@router.post("/gemini/qa", response_model=LLMResponse)
def gemini_qa(request: LLMRequest):
    # 요청의 기능 유형을 질의응답으로 고정합니다.
    request.task_type = "qa"
    # 공통 Gemini 실행 함수를 재사용합니다.
    return run_gemini(request)


# 요약 전용 Gemini 엔드포인트입니다.
@router.post("/gemini/summary", response_model=LLMResponse)
def gemini_summary(request: LLMRequest):
    # 요청의 기능 유형을 요약으로 고정합니다.
    request.task_type = "summary"
    # 공통 Gemini 실행 함수를 재사용합니다.
    return run_gemini(request)


# 번역 전용 Gemini 엔드포인트입니다.
@router.post("/gemini/translation", response_model=LLMResponse)
def gemini_translation(request: LLMRequest):
    # 요청의 기능 유형을 번역으로 고정합니다.
    request.task_type = "translation"
    # 공통 Gemini 실행 함수를 재사용합니다.
    return run_gemini(request)


# 채팅 전용 Gemini 엔드포인트입니다.
@router.post("/gemini/chat", response_model=LLMResponse)
def gemini_chat(request: LLMRequest):
    # 요청의 기능 유형을 채팅으로 고정합니다.
    request.task_type = "chat"
    # 공통 Gemini 실행 함수를 재사용합니다.
    return run_gemini(request)


# 다양한 Use Case 전용 Gemini 엔드포인트입니다.
@router.post("/gemini/usecase", response_model=LLMResponse)
def gemini_usecase(request: LLMRequest):
    # 요청의 기능 유형을 Use Case로 고정합니다.
    request.task_type = "usecase"
    # 공통 Gemini 실행 함수를 재사용합니다.
    return run_gemini(request)
