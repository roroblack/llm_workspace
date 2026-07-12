"""에이전트 응답 스키마."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class AgentStep(BaseModel):
    step: int
    action: str
    action_input: dict[str, Any]
    observation: dict[str, Any]


class AgentResponse(BaseModel):
    answer: str
    steps: list[AgentStep]
    stopped_by: str  # final_answer / duplicate_tool_call / max_steps
