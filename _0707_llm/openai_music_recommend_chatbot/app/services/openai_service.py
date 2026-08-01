import logging

from openai import OpenAI

from app.core.config import Settings


logger = logging.getLogger(__name__)


class OpenAIChatService:
    """
    OpenAI ChatGPT API 호출을 담당하는 서비스 클래스입니다.

    FastAPI 라우터가 직접 OpenAI API를 호출하지 않고
    이 서비스 클래스를 거치도록 만들면 코드 역할이 명확해집니다.
    """

    def __init__(self, settings: Settings):
        """
        서비스 초기화 함수입니다.

        settings:
            .env 파일에서 읽은 OpenAI API Key, 모델명, 토큰 설정 등을 포함합니다.
        """

        # 설정 객체를 인스턴스 변수에 저장합니다.
        self.settings = settings

        # OpenAI API Key가 비어 있으면 클라이언트를 만들지 않습니다.
        # 이렇게 하면 API Key 없이도 추천 로직과 UI 화면은 확인할 수 있습니다.
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

    def _is_reasoning_model(self, model: str) -> bool:
        """
        temperature/top_p를 지원하지 않는 reasoning 계열 모델인지 판단합니다.

        gpt-5, gpt-5.5, o1, o3, o4 계열은 일부 샘플링 파라미터를
        지원하지 않을 수 있으므로 요청 파라미터를 분기합니다.
        """

        # 모델명을 소문자로 변환합니다.
        normalized_model = model.lower()

        # reasoning 성격의 모델 prefix를 튜플로 정의합니다.
        reasoning_prefixes = ("gpt-5", "o1", "o3", "o4")

        # 모델명이 해당 prefix 중 하나로 시작하는지 반환합니다.
        return normalized_model.startswith(reasoning_prefixes)

    def build_music_prompt(self, user_message: str, detected_mood: str, recommendations: list[dict]) -> str:
        """
        OpenAI에 전달할 음악 추천용 Prompt를 구성합니다.
        """

        # 추천 음악 목록을 사람이 읽기 쉬운 문자열로 변환합니다.
        song_lines = []

        # 추천 음악을 순서대로 반복합니다.
        for index, song in enumerate(recommendations, start=1):
            # 각 음악의 제목, 가수, 감정, 이유, URL을 한 줄로 정리합니다.
            song_lines.append(
                f"{index}. 제목: {song['title']} / 가수: {song['artist']} / "
                f"감정: {song['mood']} / 추천이유: {song['reason']} / URL: {song['url']}"
            )

        # 리스트를 줄바꿈 문자열로 합칩니다.
        songs_text = "\n".join(song_lines)

        # ChatGPT에게 줄 작업 지시 Prompt를 작성합니다.
        return f"""
사용자 입력:
{user_message}

PyTorch 추천 모델이 추정한 대표 감정:
{detected_mood}

PyTorch 추천 모델이 선택한 음악 목록:
{songs_text}

위 정보를 바탕으로 사용자에게 음악 추천 챗봇처럼 답변하시오.

답변 규칙:
1. 먼저 사용자의 감정을 공감하시오.
2. 추천 음악 3개를 번호 목록으로 제시하시오.
3. 각 음악마다 추천 이유를 짧게 설명하시오.
4. URL은 그대로 포함하시오.
5. 저작권이 있는 음악 또는 영상은 원저작자와 플랫폼 정책을 확인해야 한다는 안내를 마지막에 한 문장으로 포함하시오.
"""

    def generate_music_answer(
        self,
        user_message: str,
        detected_mood: str,
        recommendations: list[dict],
        conversation_history: list[dict] | None = None,
    ) -> str:
        """
        OpenAI API로 자연어 음악 추천 답변을 생성합니다.

        API Key가 없는 경우에도 앱 실습이 가능하도록
        PyTorch 추천 결과만으로 기본 답변을 생성하는 fallback을 제공합니다.
        """

        # OpenAI API Key가 없거나 클라이언트가 생성되지 않았으면 fallback 답변을 반환합니다.
        if self.client is None:
            return self._fallback_answer(user_message, detected_mood, recommendations)

        # OpenAI에 전달할 사용자 Prompt를 생성합니다.
        prompt = self.build_music_prompt(user_message, detected_mood, recommendations)

        # 시스템 지시문을 작성합니다.
        instructions = """
당신은 사용자의 감정을 이해하고 상황에 맞는 음악을 추천하는 친절한 음악 추천 챗봇입니다.
답변은 한국어로 작성합니다.
사용자가 힘든 감정을 표현하면 과장하지 말고 따뜻하게 공감합니다.
추천 결과는 PyTorch 추천 모델의 결과를 우선 사용합니다.
"""

        # OpenAI Responses API 요청 파라미터의 공통 부분을 구성합니다.
        request_params = {
            "model": self.settings.OPENAI_MODEL,
            "instructions": instructions,
            "input": prompt,
            "max_output_tokens": self.settings.OPENAI_MAX_OUTPUT_TOKENS,
        }

        # reasoning 모델이면 temperature/top_p를 보내지 않습니다.
        if self._is_reasoning_model(self.settings.OPENAI_MODEL):
            # reasoning 모델에는 추론 노력 수준을 낮게 지정하여 응답 속도를 높입니다.
            request_params["reasoning"] = {"effort": "low"}
        else:
            # 일반 모델은 temperature와 top_p를 함께 전달할 수 있습니다.
            request_params["temperature"] = self.settings.OPENAI_TEMPERATURE
            request_params["top_p"] = self.settings.OPENAI_TOP_P

        # OpenAI Responses API를 호출합니다.
        try:
            response = self.client.responses.create(**request_params)
        except Exception:
            logger.exception("OpenAI response generation failed; using fallback answer.")
            return self._fallback_answer(user_message, detected_mood, recommendations)

        # SDK가 제공하는 output_text 속성에서 최종 텍스트를 반환합니다.
        return response.output_text

    def _fallback_answer(self, user_message: str, detected_mood: str, recommendations: list[dict]) -> str:
        """
        OpenAI API Key가 없을 때 사용할 기본 답변 생성 함수입니다.

        이 함수는 외부 API를 호출하지 않고 추천 결과를 문자열로 조합합니다.
        """

        # 답변의 첫 문장을 만듭니다.
        lines = [
            f"입력하신 문장에서 '{detected_mood}' 분위기가 느껴집니다.",
            "아래 음악을 추천합니다.",
            "",
        ]

        # 추천 음악을 번호 목록으로 추가합니다.
        for index, song in enumerate(recommendations, start=1):
            lines.append(f"{index}. {song['title']} - {song['artist']}")
            lines.append(f"   추천 이유: {song['reason']}")
            lines.append(f"   URL: {song['url']}")
            lines.append("")

        # 저작권 안내 문장을 마지막에 추가합니다.
        lines.append("음악과 영상 URL을 사용할 때는 원저작자와 플랫폼의 저작권 정책을 확인해야 합니다.")

        # 줄바꿈으로 연결해 최종 답변을 반환합니다.
        return "\n".join(lines)
