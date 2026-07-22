# -*- coding: utf-8 -*-
"""ReAct 에이전트와 MCP 서버가 공통으로 사용하는 LangChain 도구 정의입니다."""

# ContextVar는 요청마다 선택한 공급자 값을 안전하게 보관합니다.
from contextvars import ContextVar
# Literal은 공급자 값을 제한합니다.
from typing import Literal

# tool 데코레이터는 일반 함수를 LLM 호출 가능 도구로 바꿉니다.
from langchain_core.tools import tool

# CSV 기반 비즈니스 로직을 가져옵니다.
from app.services.data_service import get_order_status, get_stock, request_exchange, search_faq
# 정책 RAG 검색 서비스를 가져옵니다.
from app.services.rag_service import search_policy

# current_provider는 현재 요청에서 정책 검색에 사용할 임베딩 공급자를 보관합니다.
current_provider: ContextVar[Literal["openai", "gemini"]] = ContextVar(
    "current_provider",
    default="openai",
)


# order_status_tool은 주문 질문을 처리하는 읽기 도구입니다.
@tool("get_order_status")
def order_status_tool(order_id: str) -> str:
    """주문번호로 실제 orders.csv의 상품, 금액, 주문일, 배송 상태를 조회한다."""
    # 서비스 함수에 주문번호를 전달하고 결과를 그대로 반환합니다.
    return get_order_status(order_id)


# stock_tool은 재고 질문을 처리하는 읽기 도구입니다.
@tool("get_stock")
def stock_tool(product_name: str) -> str:
    """상품명으로 실제 inventory.csv의 현재 재고 수량을 조회한다."""
    # 서비스 함수에 상품명을 전달하고 실제 재고 결과를 반환합니다.
    return get_stock(product_name)


# faq_tool은 자주 묻는 질문을 검색하는 읽기 도구입니다.
@tool("search_faq")
def faq_tool(keyword: str) -> str:
    """배송, 결제, 회원, 주문 등 자주 묻는 질문을 faq.csv에서 검색한다."""
    # FAQ 서비스 함수에 검색어를 전달합니다.
    return search_faq(keyword)


# policy_tool은 RAG 검색기를 ReAct 도구로 노출합니다.
@tool("policy_search")
def policy_tool(query: str) -> str:
    """환불, 교환, 멤버십 등 사내 정책 PDF에서 근거 문서를 검색한다."""
    # 현재 요청의 공급자 값을 ContextVar에서 읽습니다.
    provider = current_provider.get()
    # 정책 검색 서비스에 질문과 공급자를 전달합니다.
    return search_policy(query, provider)


# exchange_tool은 실제 주문을 확인한 뒤 교환을 접수하는 쓰기 행동 도구입니다.
@tool("request_exchange")
def exchange_tool(order_id: str, reason: str) -> str:
    """고객의 명시적 교환 요청을 접수하고 EX 접수번호를 반환한다."""
    # 주문번호와 교환 사유를 서비스 함수에 전달합니다.
    return request_exchange(order_id, reason)


# ALL_TOOLS는 ReAct 에이전트가 선택할 수 있는 전체 도구 목록입니다.
ALL_TOOLS = [order_status_tool, stock_tool, faq_tool, policy_tool, exchange_tool]
