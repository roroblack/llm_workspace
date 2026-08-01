# -*- coding: utf-8 -*-
"""역할별 전문 에이전트가 검색 근거를 사용해 답변을 생성합니다."""
from app.llm.factory import create_chat_model, message_text
from app.vectordb.chroma_store import ChromaStore

class AgentService:
    def __init__(self) -> None:
        self.store = ChromaStore()

    def answer(self, question: str, route: str, provider: str) -> tuple[str, list[str]]:
        source = "faq" if route == "policy" else "products"
        hits = self.store.search(question, source=source, limit=3)
        evidence = [hit["document"] for hit in hits]
        if not evidence:
            return "검색 근거가 없습니다. 먼저 /api/vector/ingest를 실행해 주세요.", []
        role = "정책/FAQ 안내 전문가" if route == "policy" else "상품 추천 전문가"
        prompt = f"너는 {role}다. 아래 검색 근거만 사용해 한국어로 답하라. 근거에 없는 사실은 만들지 마라.\n\n질문: {question}\n\n검색 근거:\n" + "\n---\n".join(evidence)
        llm = create_chat_model(provider, temperature=0.1)
        return message_text(llm.invoke(prompt)), evidence
