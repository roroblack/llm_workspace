"""에이전트 라우터 통합 테스트 (모델 없이, run_react_agent monkeypatch)."""

from app.agent.schemas import AgentResponse, AgentStep


def test_agent_chat_endpoint(client, monkeypatch):
    from app.routers import agent as agent_router

    def fake(question, db, max_steps=3):
        return AgentResponse(
            answer="가격은 79000원입니다.",
            steps=[
                AgentStep(
                    step=1,
                    action="get_price",
                    action_input={"product_code": "P0001"},
                    observation={"ok": True, "price": 79000},
                )
            ],
            stopped_by="final_answer",
        )

    monkeypatch.setattr(agent_router, "run_react_agent", fake)
    r = client.post("/api/agent/chat", json={"question": "P0001 가격?", "max_steps": 2})
    assert r.status_code == 200
    body = r.json()
    assert body["stopped_by"] == "final_answer"
    assert len(body["steps"]) == 1
    assert body["steps"][0]["action"] == "get_price"


def test_agent_chat_validation(client):
    r = client.post("/api/agent/chat", json={"question": "", "max_steps": 2})
    assert r.status_code == 422  # 빈 question
