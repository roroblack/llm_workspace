# -*- coding: utf-8 -*-
"""LLM 파라미터를 바꿔가며 응답을 비교해보는 실습 실행 파일입니다."""

# 패키지 형태(python -m src.main)와 직접 실행(python src/main.py)을 모두 지원하기 위한 분기입니다.
try:
    # 패키지로 실행될 때는 상대 경로로 하위 모듈을 불러옵니다.
    from llm_app import config
    from llm_app.llm_service import ask_gemini, ask_openai
    from llm_app.utils import ask_float, ask_int, print_header, print_result
except ImportError:
    # 직접 실행될 때를 대비해 현재 폴더를 모듈 검색 경로에 추가합니다.
    import sys
    from pathlib import Path

    # 이 파일이 있는 src 폴더를 모듈 검색 경로 맨 앞에 넣습니다.
    sys.path.insert(0, str(Path(__file__).resolve().parent))

    # 경로를 추가한 뒤 다시 하위 모듈을 불러옵니다.
    from llm_app import config
    from llm_app.llm_service import ask_gemini, ask_openai
    from llm_app.utils import ask_float, ask_int, print_header, print_result


def choose_provider() -> str:
    """어떤 LLM 서비스를 사용할지 사용자에게 선택받습니다."""

    # 올바른 선택이 들어올 때까지 반복합니다.
    while True:
        # 사용할 서비스를 번호로 입력받습니다.
        raw = input("사용할 서비스를 선택하세요 [1] Gemini  [2] OpenAI (기본값 1): ").strip()

        # 입력이 없거나 1이면 Gemini를 사용합니다.
        if raw in ("", "1"):
            return "gemini"

        # 2를 입력하면 OpenAI를 사용합니다.
        if raw == "2":
            return "openai"

        # 그 외의 값이면 다시 입력받습니다.
        print("1 또는 2를 입력해 주세요.")


def main() -> None:
    """실습 프로그램의 전체 흐름을 담당하는 진입 함수입니다."""

    # 프로그램 제목을 출력합니다.
    print_header("LLM 파라미터 실습 프로젝트")

    # 현재 환경 설정 상태를 확인해 출력합니다.
    status = config.get_env_status()

    # .env 파일 인식 여부와 모델명을 안내합니다.
    print(f".env 파일 인식: {status['env_file_exists']}")
    print(f"Gemini 모델: {status['gemini_model']} / OpenAI 모델: {status['openai_model']}")
    print(f"Gemini Key 로드: {status['google_api_key_loaded']} / OpenAI Key 로드: {status['openai_api_key_loaded']}")

    # 사용할 서비스를 선택받습니다.
    provider = choose_provider()

    # 모델에 보낼 프롬프트(질문)를 입력받습니다.
    prompt = input("\n프롬프트를 입력하세요: ").strip()

    # 프롬프트가 비어 있으면 기본 예시 문장을 사용합니다.
    if not prompt:
        prompt = "인공지능을 초등학생도 이해할 수 있게 한 문장으로 설명해줘."
        print(f"입력이 없어 기본 프롬프트를 사용합니다: {prompt}")

    # 창의성을 조절하는 temperature 값을 입력받습니다.
    temperature = ask_float("temperature 값", default=0.7, low=0.0, high=2.0)

    # 후보 단어 범위를 조절하는 top_p 값을 입력받습니다.
    top_p = ask_float("top_p 값", default=0.9, low=0.0, high=1.0)

    # 최대 생성 토큰 수를 입력받습니다.
    max_tokens = ask_int("최대 토큰 수", default=512, low=1, high=8192)

    # 선택한 서비스에 맞춰 실제 호출을 수행합니다.
    try:
        # Gemini를 선택한 경우 Gemini 호출 함수를 사용합니다.
        if provider == "gemini":
            answer = ask_gemini(
                prompt,
                temperature=temperature,
                top_p=top_p,
                max_output_tokens=max_tokens,
            )
            # Gemini 응답을 출력합니다.
            print_result(f"Gemini ({config.GEMINI_MODEL})", answer)

        # OpenAI를 선택한 경우 OpenAI 호출 함수를 사용합니다.
        else:
            answer = ask_openai(
                prompt,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
            )
            # OpenAI 응답을 출력합니다.
            print_result(f"OpenAI ({config.OPENAI_MODEL})", answer)

    # 환경변수 누락 등 설정 오류는 사용자에게 친절하게 안내합니다.
    except RuntimeError as error:
        print(f"\n[설정 오류] {error}")

    # 그 외 네트워크나 API 오류는 원인을 함께 보여줍니다.
    except Exception as error:  # noqa: BLE001 - 실습 편의를 위해 모든 예외를 안내합니다.
        print(f"\n[호출 오류] 호출 중 문제가 발생했습니다: {error}")


# 이 파일을 직접 실행했을 때만 main 함수를 호출합니다.
if __name__ == "__main__":
    main()
