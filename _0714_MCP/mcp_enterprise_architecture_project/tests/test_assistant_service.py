"""OpenAI Responses API와 MCP Tool 오케스트레이션을 검사합니다."""

import asyncio
import json
from types import SimpleNamespace

from app.services.assistant_service import AssistantService


class FakeMCPClient:
    """테스트용 MCP Tool 목록과 실행 결과를 반환합니다."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    async def list_tools(self) -> list[dict]:
        return [
            {
                "name": "file_list",
                "description": "파일 목록을 반환합니다.",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "file_read",
                "description": "파일을 읽습니다.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"filename": {"type": "string"}},
                    "required": ["filename"],
                },
            },
        ]

    async def call_tool(self, name: str, arguments: dict) -> dict:
        self.calls.append((name, arguments))
        return {"tool": name, "arguments": arguments}


class FakeResponses:
    """준비된 OpenAI 응답을 순서대로 반환합니다."""

    def __init__(self, responses: list[SimpleNamespace]) -> None:
        self._responses = responses
        self.calls: list[dict] = []

    async def create(self, **kwargs) -> SimpleNamespace:
        self.calls.append(kwargs)
        return self._responses.pop(0)


def response(response_id: str, output: list, text: str = "") -> SimpleNamespace:
    """테스트용 Responses API 응답 객체를 만듭니다."""

    return SimpleNamespace(id=response_id, output=output, output_text=text)


def function_call(name: str, arguments: dict, call_id: str) -> SimpleNamespace:
    """테스트용 함수 호출 출력 항목을 만듭니다."""

    return SimpleNamespace(
        type="function_call",
        name=name,
        arguments=json.dumps(arguments),
        call_id=call_id,
    )


def test_assistant_runs_multiple_openai_tool_rounds() -> None:
    """OpenAI가 요청한 MCP Tool을 여러 라운드에 걸쳐 실행해야 합니다."""

    asyncio.run(_run_multiple_openai_tool_rounds())


async def _run_multiple_openai_tool_rounds() -> None:
    """다단계 Tool 호출 시나리오를 비동기로 실행합니다."""

    mcp_client = FakeMCPClient()
    fake_responses = FakeResponses(
        [
            response("resp-1", [function_call("file_list", {}, "call-1")]),
            response(
                "resp-2",
                [function_call("file_read", {"filename": "welcome.txt"}, "call-2")],
            ),
            response("resp-3", [], "welcome.txt의 내용을 확인했습니다."),
        ]
    )

    service = AssistantService()
    service.mcp_client = mcp_client
    service.openai = SimpleNamespace(responses=fake_responses)

    result = await service.ask("문서 목록을 보고 welcome.txt를 읽어줘.")

    assert result["mode"] == "openai"
    assert result["tool_rounds"] == 2
    assert result["answer"] == "welcome.txt의 내용을 확인했습니다."
    assert mcp_client.calls == [
        ("file_list", {}),
        ("file_read", {"filename": "welcome.txt"}),
    ]
    assert [item["round"] for item in result["tool_trace"]] == [1, 2]
    assert fake_responses.calls[1]["previous_response_id"] == "resp-1"
    assert fake_responses.calls[2]["previous_response_id"] == "resp-2"
    assert fake_responses.calls[1]["tool_choice"] == "auto"


def test_assistant_returns_openai_text_without_tool_call() -> None:
    """Tool이 필요하지 않으면 OpenAI 텍스트를 바로 반환해야 합니다."""

    asyncio.run(_run_openai_text_without_tool_call())


async def _run_openai_text_without_tool_call() -> None:
    """Tool 없는 텍스트 응답 시나리오를 비동기로 실행합니다."""

    fake_responses = FakeResponses([response("resp-1", [], "안녕하세요!")])
    service = AssistantService()
    service.mcp_client = FakeMCPClient()
    service.openai = SimpleNamespace(responses=fake_responses)

    result = await service.ask("안녕")

    assert result["answer"] == "안녕하세요!"
    assert result["tool_rounds"] == 0
    assert result["tool_trace"] == []
