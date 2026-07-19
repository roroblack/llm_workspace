"""로컬 Gemma 실호출 스모크 (수동, CI 제외).

실행: 로컬 모델 서버 기동 후
    pytest -m llm tests/test_react_live.py
"""

import pytest

from app.agent.react import run_react_agent
from app.db.database import SessionLocal


@pytest.mark.llm
def test_live_agent_answers():
    db = SessionLocal()
    try:
        res = run_react_agent("P0001 상품 가격 알려줘", db, max_steps=3)
        # 내용은 비결정적이라 답변 문자열 존재만 확인
        assert isinstance(res.answer, str)
        assert res.stopped_by in {"final_answer", "max_steps", "duplicate_tool_call"}
    finally:
        db.close()
