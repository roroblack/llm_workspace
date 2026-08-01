# -*- coding: utf-8 -*-
"""웹 검색 에이전트, 네트워크 폴백, 마크다운 저장 기능을 제공합니다."""

# 날짜가 포함된 파일명을 만들기 위해 datetime을 가져옵니다.
import datetime
# 안전한 파일 경로 조작을 위해 pathlib을 사용합니다.
import pathlib
# 실행 시간을 측정하기 위해 time 모듈을 사용합니다.
import time

# 제공된 공통 모듈에서 LLM 생성 함수를 가져옵니다.
from common import get_chat
# 메뉴에서 선택한 공급자를 읽기 위해 실행 컨텍스트 함수를 가져옵니다.
from app_context import get_provider
# 서로 다른 모델 응답을 문자열로 통일하기 위한 공통 함수를 가져옵니다.
from message_utils import extract_text, last_message_text

# 프로젝트의 루트 경로를 계산합니다.
ROOT = pathlib.Path(__file__).resolve().parent.parent
# 생성된 마크다운 보고서를 저장할 폴더 경로입니다.
REPORTS = ROOT / "reports"


def _build_search_tool():
    """API 키가 필요 없는 DuckDuckGo 검색 도구 인스턴스를 생성합니다."""
    # 패키지가 없을 때 앱 시작 전체가 실패하지 않도록 함수 내부에서 지연 임포트합니다.
    from langchain_community.tools import DuckDuckGoSearchResults

    # 검색 결과에 제목, 스니펫, 링크가 포함되는 LangChain 도구를 반환합니다.
    return DuckDuckGoSearchResults()


def build_research_agent():
    """검색 도구를 스스로 호출하는 시장 조사 에이전트를 생성합니다."""
    # create_agent도 실제 메뉴 실행 시에만 필요하므로 지연 임포트합니다.
    from langchain.agents import create_agent

    # 사용자가 선택한 OpenAI 또는 Gemini 모델을 temperature 0.3으로 생성합니다.
    # 리포트는 사실성을 유지하면서도 자연스러운 서술이 필요하므로 낮은 창의성을 사용합니다.
    llm = get_chat(provider=get_provider(), temperature=0.3)

    # 최신 정보를 수집할 DuckDuckGo 검색 도구를 준비합니다.
    search_tool = _build_search_tool()

    # LLM과 검색 도구를 결합한 에이전트를 생성합니다.
    return create_agent(
        # 앞에서 만든 선택 공급자 기반 LLM을 전달합니다.
        llm,
        # 에이전트가 필요할 때 웹 검색을 호출할 수 있도록 도구 목록을 전달합니다.
        tools=[search_tool],
        # 역할, 조사 방식, 출력 형식을 시스템 프롬프트로 고정합니다.
        system_prompt=(
            "너는 승승장구몰의 시장 조사 애널리스트다. "
            "사용자가 요청한 주제를 반드시 웹에서 검색하여 최신 근거를 수집하라. "
            "서로 다른 검색 결과를 비교하고 과장되거나 불확실한 내용은 단정하지 마라. "
            "최종 답변은 한국어 마크다운으로 작성하고 "
            "'## 개요', '## 핵심 동향', '## 시사점', '## 참고 출처' 섹션을 포함하라. "
            "참고 출처에는 검색 결과에서 확인한 제목이나 URL을 가능한 범위에서 적어라."
        ),
    )


def llm_only_latest_demo(topic: str) -> str:
    """검색 없이 LLM에게 최신 동향을 질문하여 지식 컷오프 한계를 확인합니다."""
    # 현재 선택한 공급자의 일반 채팅 모델을 생성합니다.
    llm = get_chat(provider=get_provider(), temperature=0.2)

    # 최신 정보 여부를 명시하도록 요청하여 검색 없는 답변의 한계를 관찰합니다.
    prompt = (
        f"'{topic}'의 최신 시장 동향을 설명하라. "
        "웹 검색 도구를 사용할 수 없다는 전제에서 답하고, "
        "확실히 최신이라고 검증할 수 없는 내용은 명확히 표시하라."
    )

    # LLM을 호출하고 공급자별 응답 형식을 공통 문자열로 변환합니다.
    return extract_text(llm.invoke(prompt))


def fallback_report(topic: str, error_message: str = "") -> str:
    """검색 실패 시 LLM 내부 지식으로 임시 리포트를 생성합니다."""
    # 현재 선택한 공급자의 LLM을 검색 없이 생성합니다.
    llm = get_chat(provider=get_provider(), temperature=0.3)

    # 폴백 결과임을 숨기지 않고 주의 문구를 포함하도록 프롬프트를 구성합니다.
    prompt = (
        f"'{topic}'에 대해 아는 범위에서 한국어 마크다운 리포트를 작성하라. "
        "맨 위에 '> ⚠️ 웹 검색 실패로 작성된 임시 리포트이며 최신 정보가 아닐 수 있습니다.'를 넣어라. "
        "'## 개요', '## 핵심 동향', '## 시사점' 섹션을 정확히 포함하라. "
        "검증되지 않은 구체적 수치나 최근 사건은 임의로 만들지 마라. "
        f"검색 실패 참고 정보: {error_message[:300]}"
    )

    # 폴백 프롬프트를 실행하고 본문 문자열을 반환합니다.
    return extract_text(llm.invoke(prompt))


def research(topic: str, force_fallback: bool = False) -> tuple[str, bool]:
    """웹 검색 기반 리포트를 만들고 실패하면 폴백 리포트를 반환합니다."""
    # 빈 주제로 검색하지 않도록 앞뒤 공백을 제거합니다.
    clean_topic = topic.strip()

    # 주제가 비어 있으면 호출 비용을 쓰기 전에 명확한 오류를 발생시킵니다.
    if not clean_topic:
        raise ValueError("조사 주제를 입력해야 합니다.")

    # 폴백 동작을 교육용으로 강제 확인할 수 있는 분기입니다.
    if force_fallback:
        return fallback_report(clean_topic, "사용자가 폴백 실습을 선택했습니다."), True

    try:
        # 검색 도구를 가진 에이전트를 생성합니다.
        agent = build_research_agent()

        # 에이전트가 검색, 수집, 요약을 수행하도록 사용자 메시지를 전달합니다.
        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            f"'{clean_topic}' 주제로 최신 시장 동향 리포트를 작성해 주세요. "
                            "최신성과 사실성이 중요하므로 검색 도구를 사용하고, "
                            "중요 주장은 가능한 한 둘 이상의 결과로 확인해 주세요."
                        ),
                    }
                ]
            }
        )

        # 최종 AI 메시지를 문자열로 추출하고 폴백 여부 False와 함께 반환합니다.
        return last_message_text(result), False

    except Exception as exc:
        # 네트워크, rate limit, 패키지 오류 등 모든 외부 의존성 실패를 화면에 알립니다.
        print(f"[경고] 웹 검색 기반 조사 실패 → LLM 지식 폴백 사용: {exc}")

        # 서비스 전체가 중단되지 않도록 폴백 리포트를 생성합니다.
        return fallback_report(clean_topic, str(exc)), True


def _safe_filename(text: str, max_length: int = 40) -> str:
    """주제를 Windows에서도 사용할 수 있는 안전한 파일명 조각으로 변환합니다."""
    # 파일명에 사용할 수 없는 주요 특수문자를 밑줄로 바꾸기 위한 문자열입니다.
    invalid_chars = '<>:"/\\|?*'

    # 각 문자를 순회하며 금지 문자는 밑줄로 치환합니다.
    cleaned = "".join("_" if char in invalid_chars else char for char in text.strip())

    # 연속 공백을 밑줄 하나로 바꿔 파일명을 읽기 쉽게 만듭니다.
    cleaned = "_".join(cleaned.split())

    # 파일명이 비어 버리면 기본 이름을 사용합니다.
    if not cleaned:
        cleaned = "research"

    # 지나치게 긴 Windows 경로 문제를 줄이기 위해 길이를 제한합니다.
    return cleaned[:max_length]


def save_report(topic: str, body: str, prefix: str = "research") -> pathlib.Path:
    """리포트 본문을 제목과 생성일 헤더와 함께 UTF-8 마크다운으로 저장합니다."""
    # reports 폴더가 없으면 자동으로 생성합니다.
    REPORTS.mkdir(parents=True, exist_ok=True)

    # 오늘 날짜를 ISO 형식 문자열로 생성합니다.
    today = datetime.date.today().isoformat()

    # 같은 날 여러 번 실행해도 덮어쓰지 않도록 시각을 파일명에 추가합니다.
    now = datetime.datetime.now().strftime("%H%M%S")

    # 주제를 안전한 파일명 조각으로 변환합니다.
    topic_name = _safe_filename(topic)

    # 보고서 파일의 전체 경로를 만듭니다.
    path = REPORTS / f"{prefix}_{today}_{now}_{topic_name}.md"

    # 사람이 파일을 열었을 때 제목과 생성 정보를 즉시 확인할 수 있도록 헤더를 만듭니다.
    header = (
        f"# 시장 조사 리포트 — {topic}\n\n"
        f"> 생성일: {today} / 사용 모델 공급자: {get_provider()} / 자동 생성\n\n"
    )

    # 한글이 깨지지 않도록 UTF-8 인코딩으로 헤더와 본문을 저장합니다.
    path.write_text(header + body.strip() + "\n", encoding="utf-8")

    # 호출자가 저장 경로를 화면에 출력할 수 있도록 Path 객체를 반환합니다.
    return path


def run_research_and_save(topic: str, force_fallback: bool = False) -> tuple[str, pathlib.Path, bool, float]:
    """조사, 저장, 실행 시간 측정을 한 번에 수행하는 편의 함수입니다."""
    # 조사 시작 시각을 기록합니다.
    started = time.perf_counter()

    # 웹 검색 또는 폴백으로 리포트를 생성합니다.
    body, used_fallback = research(topic, force_fallback=force_fallback)

    # 생성된 본문을 마크다운 파일로 저장합니다.
    path = save_report(topic, body)

    # 시작부터 저장 완료까지 걸린 시간을 계산합니다.
    elapsed = time.perf_counter() - started

    # 메뉴 화면에서 사용할 모든 결과를 반환합니다.
    return body, path, used_fallback, elapsed
