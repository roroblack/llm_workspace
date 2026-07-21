# -*- coding: utf-8 -*-
"""업무별 전문 에이전트를 Agent-to-Agent 방식으로 위임하는 모듈입니다."""

# 보고서와 데이터 처리 서비스를 가져옵니다.
from app.services.business_service import format_facts, load_facts, load_facts_for_month, make_fallback_report, save_report, write_report_with_fallback
# 차트 생성 서비스를 가져옵니다.
from app.services.chart_service import add_chart_to_report, make_category_chart
# RAG 검색 서비스를 가져옵니다.
from app.services.rag_service import search_knowledge
# 채팅 모델 생성 함수를 가져옵니다.
from app.core.common import get_chat
# 모델 응답 문자열 추출 함수를 가져옵니다.
from app.services.message_utils import extract_text

# 외부에서 조회할 수 있는 전문 에이전트 카드 목록을 정의합니다.
AGENT_CARDS = [
    {"name": "sales-analyst-agent", "description": "월별 매출 수치와 카테고리 성과를 분석합니다.", "skills": ["월별 매출", "성장률", "카테고리 순위"]},
    {"name": "report-writer-agent", "description": "확정 수치만 사용해 경영진 보고서를 작성하고 저장합니다.", "skills": ["경영 보고서", "마크다운 저장", "차트 포함 보고서"]},
    {"name": "knowledge-agent", "description": "PDF와 CSV에서 내부 정책 및 제품 근거를 검색합니다.", "skills": ["RAG", "정책", "매뉴얼", "근거 검색"]},
    {"name": "strategy-agent", "description": "분석 수치와 내부 근거를 종합해 실행 제언을 작성합니다.", "skills": ["경영 전략", "마케팅", "운영 제언"]},
]


def _llm_answer(prompt: str, provider: str) -> str:
    """전문 에이전트용 공통 LLM 호출을 실행합니다."""
    # 선택한 공급자의 모델을 생성합니다.
    llm = get_chat(provider=provider, temperature=0.2)
    # 프롬프트를 모델에 전달합니다.
    response = llm.invoke(prompt)
    # 공급자별 응답 객체를 일반 문자열로 반환합니다.
    return extract_text(response)


def invoke_specialist(agent_name: str, message: str, provider: str) -> dict[str, object]:
    """지정한 전문 에이전트에 메시지를 위임하고 구조화된 결과를 반환합니다."""
    # 월 문자열이 메시지에 포함되었는지 단순 정규식으로 추출합니다.
    import re
    # YYYY-MM 형태의 첫 번째 값을 찾습니다.
    match = re.search(r"\b(20\d{2}-\d{2})\b", message)
    # 월이 있으면 해당 월을, 없으면 최신 월을 사용합니다.
    month = match.group(1) if match else ""
    # 매출 분석 에이전트는 pandas가 계산한 확정 facts를 반환합니다.
    if agent_name == "sales-analyst-agent":
        facts = load_facts_for_month(month) if month else load_facts()
        return {"agent": agent_name, "answer": format_facts(facts), "facts": facts}
    # 보고서 작성 에이전트는 보고서와 차트를 생성해 저장합니다.
    if agent_name == "report-writer-agent":
        facts = load_facts_for_month(month) if month else load_facts()
        chart_path = make_category_chart(facts)
        body = write_report_with_fallback(facts)
        report_path = save_report(facts, add_chart_to_report(body, chart_path), filename=f"monthly_sales_{facts['month']}_with_chart.md")
        return {"agent": agent_name, "answer": body, "report": report_path.name, "chart": chart_path.name}
    # 내부 지식 에이전트는 RAG 검색 결과를 근거로 답변합니다.
    if agent_name == "knowledge-agent":
        rag = search_knowledge(message, provider)
        prompt = f"아래 근거만 사용해 질문에 답하라. 근거에 없으면 확인할 수 없다고 말하라.\n질문: {message}\n\n{rag['context']}"
        answer = _llm_answer(prompt, provider)
        return {"agent": agent_name, "answer": answer, "sources": rag["sources"]}
    # 전략 에이전트는 매출 facts와 RAG 근거를 함께 사용해 실행 제언을 작성합니다.
    if agent_name == "strategy-agent":
        facts = load_facts_for_month(month) if month else load_facts()
        rag = search_knowledge(message, provider)
        prompt = f"확정 수치와 내부 근거만 사용해 실행 가능한 경영 제언을 작성하라. 숫자를 만들지 마라.\n[수치]\n{format_facts(facts)}\n\n[내부 근거]\n{rag['context']}\n\n[요청]\n{message}"
        answer = _llm_answer(prompt, provider)
        return {"agent": agent_name, "answer": answer, "facts": facts, "sources": rag["sources"]}
    # 등록되지 않은 에이전트명은 명확한 오류로 처리합니다.
    raise ValueError(f"등록되지 않은 A2A 에이전트입니다: {agent_name}")
