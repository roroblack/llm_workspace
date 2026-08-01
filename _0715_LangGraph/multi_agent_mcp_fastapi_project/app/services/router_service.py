# -*- coding: utf-8 -*-
"""규칙·LLM·하이브리드 Supervisor 라우팅을 구현합니다."""
from app.llm.factory import create_chat_model, message_text
POLICY_WORDS = ["환불", "교환", "배송", "취소", "적립", "포인트", "무료배송", "회원", "등급", "반품", "받아"]
SALES_WORDS = ["추천", "상품", "가성비", "골라", "인기", "선물", "살만"]

def route_rule(question: str) -> str:
    return "policy" if any(word in question for word in POLICY_WORDS) else "sales"

def route_llm(question: str, provider: str) -> str:
    llm = create_chat_model(provider, temperature=0.0)
    prompt = "고객 질문을 policy 또는 sales 한 단어로만 분류하라. 정책/배송/환불이면 policy, 상품 추천이면 sales.\n질문: " + question
    answer = message_text(llm.invoke(prompt)).lower()
    return "policy" if "policy" in answer else "sales"

def route_hybrid(question: str, provider: str) -> str:
    if any(word in question for word in POLICY_WORDS):
        return "policy"
    if any(word in question for word in SALES_WORDS):
        return "sales"
    return route_llm(question, provider)
