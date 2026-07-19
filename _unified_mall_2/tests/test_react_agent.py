"""수동 ReAct 루프 결정론적 테스트 (mock chat_fn, 모델 없음)."""

import json

from app.agent.react import run_react_agent
from app.db.database import SessionLocal


def _tool_call(name, args, cid="c1"):
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [{"id": cid, "name": name, "arguments": json.dumps(args)}],
    }


def _final(text):
    return {"role": "assistant", "content": text, "tool_calls": None}


def _scripted(responses):
    it = iter(responses)

    def fn(messages, tools):
        return next(it)

    return fn


def _db():
    return SessionLocal()


def test_happy_path_tool_then_final():
    db = _db()
    try:
        chat = _scripted([_tool_call("get_stock", {"product_code": "P0001"}), _final("재고 충분합니다.")])
        res = run_react_agent("P0001 재고?", db, chat_fn=chat, max_steps=3)
        assert res.stopped_by == "final_answer"
        assert res.answer == "재고 충분합니다."
        assert len(res.steps) == 1
        assert res.steps[0].action == "get_stock"
        assert res.steps[0].observation["ok"] is True
    finally:
        db.close()


def test_max_steps_reached():
    db = _db()
    counter = {"i": 0}

    def always_new(messages, tools):
        counter["i"] += 1
        return _tool_call("search_product", {"keyword": f"k{counter['i']}"}, cid=f"c{counter['i']}")

    try:
        res = run_react_agent("검색", db, chat_fn=always_new, max_steps=2)
        assert res.stopped_by == "max_steps"
        assert len(res.steps) == 2
    finally:
        db.close()


def test_duplicate_tool_call_blocked():
    db = _db()
    try:
        chat = _scripted(
            [
                _tool_call("get_price", {"product_code": "P0001"}, cid="c1"),
                _tool_call("get_price", {"product_code": "P0001"}, cid="c2"),
            ]
        )
        res = run_react_agent("가격?", db, chat_fn=chat, max_steps=4)
        assert res.stopped_by == "duplicate_tool_call"
    finally:
        db.close()


def test_unknown_tool_observation():
    db = _db()
    try:
        chat = _scripted([_tool_call("no_such_tool", {"x": 1}), _final("완료")])
        res = run_react_agent("?", db, chat_fn=chat, max_steps=3)
        assert res.steps[0].observation["ok"] is False
        assert res.steps[0].observation["error_code"] == "unknown_tool"
        assert res.stopped_by == "final_answer"
    finally:
        db.close()


def test_missing_arg_becomes_bad_arguments():
    db = _db()
    try:
        # get_price는 product_code 필수 → 빈 args면 TypeError → bad_arguments 관찰
        chat = _scripted([_tool_call("get_price", {}), _final("완료")])
        res = run_react_agent("가격?", db, chat_fn=chat, max_steps=3)
        assert res.steps[0].observation["ok"] is False
        assert res.steps[0].observation["error_code"] == "bad_arguments"
        assert res.stopped_by == "final_answer"
    finally:
        db.close()


def test_extra_arg_becomes_bad_arguments():
    db = _db()
    try:
        chat = _scripted(
            [_tool_call("get_price", {"product_code": "P0001", "foo": 1}), _final("완료")]
        )
        res = run_react_agent("가격?", db, chat_fn=chat, max_steps=3)
        assert res.steps[0].observation["error_code"] == "bad_arguments"
    finally:
        db.close()


def test_multiple_tool_calls_in_one_step():
    db = _db()

    def chat(messages, tools):
        # 한 assistant 메시지에 도구 2개
        if any(m.get("role") == "tool" for m in messages):
            return _final("둘 다 확인했습니다.")
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {"id": "c1", "name": "get_price", "arguments": json.dumps({"product_code": "P0001"})},
                {"id": "c2", "name": "get_stock", "arguments": json.dumps({"product_code": "P0001"})},
            ],
        }

    try:
        res = run_react_agent("가격과 재고?", db, chat_fn=chat, max_steps=3)
        assert len(res.steps) == 2
        actions = {s.action for s in res.steps}
        assert actions == {"get_price", "get_stock"}
        assert res.stopped_by == "final_answer"
    finally:
        db.close()


def test_message_order_assistant_before_tool():
    """assistant(tool_calls) 메시지가 tool 결과보다 먼저 쌓이는지 (OpenAI 순서)."""
    db = _db()
    captured = {}

    def chat(messages, tools):
        if any(m.get("role") == "tool" for m in messages):
            # 두 번째 호출 시점의 메시지 순서를 캡처
            captured["messages"] = list(messages)
            return _final("done")
        return _tool_call("get_price", {"product_code": "P0001"})

    try:
        run_react_agent("가격?", db, chat_fn=chat, max_steps=3)
        roles = [m["role"] for m in captured["messages"]]
        # system, user, assistant(tool_calls), tool ... 순서
        ai_idx = roles.index("assistant")
        tool_idx = roles.index("tool")
        assert ai_idx < tool_idx
    finally:
        db.close()


def test_bad_json_arguments_observation():
    db = _db()

    def chat(messages, tools):
        # arguments가 잘못된 JSON 문자열
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [{"id": "c1", "name": "get_price", "arguments": "{not valid json"}],
        }

    # 다음 스텝에서 종료시키기 위해 스크립트 조합
    responses = [
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [{"id": "c1", "name": "get_price", "arguments": "{not valid json"}],
        },
        _final("처리했습니다."),
    ]
    try:
        res = run_react_agent("가격?", db, chat_fn=_scripted(responses), max_steps=3)
        assert res.steps[0].observation["error_code"] == "bad_arguments"
        assert res.stopped_by == "final_answer"
    finally:
        db.close()
