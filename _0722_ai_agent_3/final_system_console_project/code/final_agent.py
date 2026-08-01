# -*- coding: utf-8 -*-
"""도구, 정책 RAG와 thread_id 단기 메모리를 통합한 최종 에이전트 모듈입니다."""

# LLM 호출 실패 시 재시도 간격을 두기 위해 time 모듈을 가져옵니다.
import time
# 공통 모듈의 채팅 모델 생성 함수를 가져옵니다.
from common import get_chat
# 현재 선택된 LLM 공급자를 확인하기 위해 컨텍스트 함수를 가져옵니다.
from app_context import get_provider
# 운영 설정과 로거 생성 함수를 가져옵니다.
from config_service import load_config, setup_logging
# 실데이터 조회용 LangChain 도구 세 개를 생성하는 함수를 가져옵니다.
from data_tools import build_langchain_tools
# 정책 PDF 검색 도구 빌더를 가져옵니다.
from policy_rag import build_policy_tool

# 에이전트가 지켜야 할 역할, 도구 선택, 환각 방지와 메모리 규칙을 정의합니다.
SYSTEM_PROMPT = (
    "너는 승승장구몰 통합 CS 상담원이다. 항상 친절하고 간결한 한국어로 답하라.\n"
    "- 주문 상태는 get_order_status, 재고는 get_stock, FAQ는 search_faq를 사용하라.\n"
    "- 환불, 교환, 멤버십, 배송 정책 질문은 반드시 policy_search 결과를 근거로 답하라.\n"
    "- 도구 결과에 정보가 없으면 임의로 만들지 말고 찾을 수 없다고 말하라.\n"
    "- 같은 thread_id의 이전 대화 맥락을 기억해 '아까 그 정책' 같은 표현을 해석하라."
)

# PDF 임베딩 비용이 큰 에이전트를 최초 한 번만 만들기 위한 모듈 캐시입니다.
_AGENT = None
# 공급자 변경 시 기존 에이전트를 다시 만들기 위해 캐시에 사용된 공급자도 보관합니다.
_AGENT_PROVIDER = None


def reset_agent() -> None:
    """공급자 변경 또는 재빌드 요청 시 기존 에이전트 캐시를 비웁니다."""
    # 함수에서 모듈 전역 에이전트 변수를 변경할 수 있도록 선언합니다.
    global _AGENT, _AGENT_PROVIDER
    # 기존 에이전트 객체 참조를 제거합니다.
    _AGENT = None
    # 기존 공급자 정보도 함께 제거합니다.
    _AGENT_PROVIDER = None


def build_agent():
    """OpenAI/Gemini LLM, 도구 4개, InMemorySaver를 결합한 단일 에이전트를 생성합니다."""
    # 최신 LangChain 에이전트 생성 함수를 가져옵니다.
    from langchain.agents import create_agent
    # thread_id별 대화 상태를 메모리에 저장하는 체크포인터를 가져옵니다.
    from langgraph.checkpoint.memory import InMemorySaver

    # data/config.yaml의 운영 설정을 읽습니다.
    config = load_config()
    # 콘솔과 파일에 동시에 기록되는 구조적 로거를 만듭니다.
    logger = setup_logging(config)
    # 현재 사용자가 선택한 공급자를 읽습니다.
    provider = get_provider()
    # 선택 공급자와 설정 temperature로 채팅 모델 객체를 생성합니다.
    llm = get_chat(provider=provider, temperature=float(config["llm"]["temperature"]))
    # 주문, 재고, FAQ 실데이터 도구 세 개를 생성합니다.
    tools = build_langchain_tools()
    # 정책 PDF를 임베딩한 RAG 도구를 네 번째 도구로 추가합니다.
    tools.append(build_policy_tool(config, logger))
    # 네 도구와 메모리, 시스템 프롬프트를 가진 단일 에이전트를 생성합니다.
    agent = create_agent(llm, tools=tools, system_prompt=SYSTEM_PROMPT, checkpointer=InMemorySaver())
    # 구성 결과를 운영 로그에 기록합니다.
    logger.info("통합 에이전트 구성 완료: provider=%s, tools=%s", provider, len(tools))
    # 에이전트와 함께 재사용할 설정과 로거를 튜플로 반환합니다.
    return agent, config, logger


def get_agent_bundle():
    """현재 공급자에 맞는 에이전트를 최초 한 번만 생성하고 이후 재사용합니다."""
    # 함수 안에서 모듈 캐시를 갱신하기 위해 전역 변수를 선언합니다.
    global _AGENT, _AGENT_PROVIDER
    # 현재 공급자를 읽어 기존 캐시와 비교합니다.
    current_provider = get_provider()
    # 캐시가 비었거나 공급자가 바뀌었으면 에이전트를 새로 구성합니다.
    if _AGENT is None or _AGENT_PROVIDER != current_provider:
        # 새 에이전트, 설정과 로거를 구성해 하나의 튜플로 저장합니다.
        _AGENT = build_agent()
        # 새 캐시가 어떤 공급자로 만들어졌는지 기록합니다.
        _AGENT_PROVIDER = current_provider
    # 재사용 가능한 에이전트 번들을 반환합니다.
    return _AGENT


def _extract_last_text(result) -> str:
    """LangChain 에이전트 결과에서 마지막 AI 답변 문자열을 안전하게 추출합니다."""
    # 딕셔너리 결과에서 messages 목록을 가져옵니다.
    messages = result.get("messages", []) if isinstance(result, dict) else []
    # 가장 마지막 메시지부터 역순으로 확인합니다.
    for message in reversed(messages):
        # LangChain 메시지 객체의 content 속성을 가져옵니다.
        content = getattr(message, "content", None)
        # content가 비어 있지 않은 문자열이면 그대로 반환합니다.
        if isinstance(content, str) and content.strip():
            return content.strip()
        # content가 블록 리스트인 모델 응답도 처리합니다.
        if isinstance(content, list):
            # 텍스트 블록의 text 값을 모아 하나의 문자열로 만듭니다.
            texts = [str(block.get("text", "")) for block in content if isinstance(block, dict) and block.get("text")]
            # 텍스트가 하나 이상 있으면 줄바꿈으로 연결해 반환합니다.
            if texts:
                return "\n".join(texts)
    # 어떤 형태에서도 답변을 찾지 못하면 결과 전체를 문자열로 변환합니다.
    return str(result)


def answer(message: str, thread_id: str = "demo") -> str:
    """동일 thread_id의 대화 맥락을 유지하면서 견고하게 최종 답변을 생성합니다."""
    # 에이전트, 설정, 로거를 캐시에서 가져오거나 최초 생성합니다.
    agent, config, logger = get_agent_bundle()
    # 재시도 횟수를 설정 파일에서 읽어 정수로 변환합니다.
    max_retries = int(config["llm"]["max_retries"])
    # 1회부터 최대 재시도 횟수까지 반복합니다.
    for attempt in range(1, max_retries + 1):
        # 외부 API 호출 중 발생할 수 있는 예외를 처리하기 위해 try 블록을 시작합니다.
        try:
            # 어떤 세션의 몇 번째 시도인지 로그에 남깁니다.
            logger.info("에이전트 호출 시도 %s/%s: thread=%s", attempt, max_retries, thread_id)
            # LangGraph checkpointer가 인식할 thread_id 설정을 구성합니다.
            runtime_config = {"configurable": {"thread_id": thread_id}}
            # 사용자 메시지를 HumanMessage 호환 딕셔너리 형식으로 전달해 에이전트를 실행합니다.
            result = agent.invoke({"messages": [{"role": "user", "content": message}]}, config=runtime_config)
            # 성공 사실을 로그에 남깁니다.
            logger.info("에이전트 호출 성공: thread=%s", thread_id)
            # 결과에서 최종 자연어 답변을 추출해 반환합니다.
            return _extract_last_text(result)
        # 네트워크, API 제한, 모델 오류 등 모든 호출 예외를 잡습니다.
        except Exception as error:
            # 지수 백오프 간격을 1, 2, 4초 순서로 계산합니다.
            wait_seconds = 2 ** (attempt - 1)
            # 예외 내용과 다음 재시도 시간을 경고 로그로 기록합니다.
            logger.warning("에이전트 호출 실패 %s회: %s, %s초 후 재시도", attempt, error, wait_seconds)
            # 마지막 시도가 아니라면 계산된 시간만큼 대기합니다.
            if attempt < max_retries:
                time.sleep(wait_seconds)
    # 모든 시도가 실패한 사실을 오류 로그로 남깁니다.
    logger.error("에이전트 호출 최종 실패: thread=%s", thread_id)
    # 프로그램을 종료하지 않고 사용자에게 재시도를 요청하는 폴백 문구를 반환합니다.
    return "죄송합니다. 일시적인 오류로 답변을 생성하지 못했습니다. 잠시 후 다시 시도해 주세요."
