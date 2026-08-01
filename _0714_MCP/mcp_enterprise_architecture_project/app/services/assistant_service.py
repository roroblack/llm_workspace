"""
사용자 질문을 OpenAI에 전달하고 MCP Tool 호출을 연결하는 Assistant 서비스입니다.
"""

# JSON 문자열을 처리하기 위해 json을 가져옵니다.
import json

# 비동기 OpenAI 클라이언트를 가져옵니다.
from openai import AsyncOpenAI

# 설정을 가져옵니다.
from app.core.settings import get_settings

# MCP Client 서비스를 가져옵니다.
from mcp_client.client import MCPClientService


# Assistant 서비스를 정의합니다.
class AssistantService:
    """OpenAI가 선택한 MCP Tool을 실행하고 최종 답변을 생성합니다."""

    # 최초 요청과 Tool 결과 후속 요청에 공통으로 적용할 지침입니다.
    INSTRUCTIONS = (
        "당신은 MCP 기반 업무 Assistant입니다. "
        "필요할 때만 제공된 Tool을 사용하고 Tool 결과를 사실 근거로 한국어로 답하세요. "
        "Tool 실행이 실패하면 실패 사실과 원인을 숨기지 마세요. "
        "파일 쓰기, GitHub Issue 생성, Slack 전송, Email 전송처럼 외부 상태를 "
        "변경하는 작업은 사용자가 대상과 내용을 명확히 요청한 경우에만 수행하세요."
    )

    # 필요한 클라이언트를 초기화합니다.
    def __init__(self) -> None:
        # 설정을 가져옵니다.
        self.settings = get_settings()

        # MCP Client 서비스를 생성합니다.
        self.mcp_client = MCPClientService()

        # OpenAI API 키가 있을 때만 클라이언트를 생성합니다.
        self.openai = (
            AsyncOpenAI(api_key=self.settings.openai_api_key)
            if self.settings.openai_api_key
            else None
        )

    # MCP Tool 목록을 OpenAI 함수 Tool 형식으로 변환합니다.
    async def _openai_tools(self) -> list[dict]:
        """MCP Tool 스키마를 OpenAI Responses API Tool 형식으로 변환합니다."""

        # MCP 서버에서 Tool 목록을 읽습니다.
        tools = await self.mcp_client.list_tools()

        # OpenAI 함수 Tool 정의 목록으로 변환합니다.
        return [
            {
                "type": "function",
                "name": item["name"],
                "description": item["description"] or "",
                "parameters": item["inputSchema"],
                "strict": False,
            }
            for item in tools
        ]

    # 사용자 질문을 처리합니다.
    async def ask(self, message: str) -> dict:
        """OpenAI와 MCP Tool을 연결하여 답변을 생성합니다."""

        # API 키가 없으면 사용 가능한 Tool 안내를 반환합니다.
        if self.openai is None:
            tools = await self.mcp_client.list_tools()
            return {
                "mode": "local",
                "answer": (
                    "OPENAI_API_KEY가 설정되지 않아 자동 Tool 선택은 생략했습니다. "
                    "아래 Tool 목록에서 원하는 Tool을 /api/mcp/call로 직접 실행할 수 있습니다."
                ),
                "tools": [tool["name"] for tool in tools],
            }

        # MCP Tool 목록을 OpenAI Tool 형식으로 변환합니다.
        tools = await self._openai_tools()

        # 최초 사용자 요청을 Responses API에 전달합니다.
        response = await self.openai.responses.create(
            model=self.settings.openai_model,
            instructions=self.INSTRUCTIONS,
            input=message,
            tools=tools,
        )

        # 실행된 Tool 기록을 저장합니다.
        tool_trace: list[dict] = []

        # Tool 결과를 바탕으로 다른 Tool이 더 필요할 수 있으므로 제한된 반복 루프를 실행합니다.
        for round_number in range(1, self.settings.openai_max_tool_rounds + 1):
            # 현재 응답에서 함수 호출 항목만 추출합니다.
            function_calls = [
                item for item in response.output if item.type == "function_call"
            ]

            # Tool 호출이 없으면 OpenAI의 최종 텍스트를 반환합니다.
            if not function_calls:
                return {
                    "mode": "openai",
                    "model": self.settings.openai_model,
                    "answer": response.output_text,
                    "tool_rounds": round_number - 1,
                    "tool_trace": tool_trace,
                }

            # 이번 라운드의 Tool 결과를 OpenAI 후속 입력으로 구성합니다.
            tool_outputs: list[dict] = []

            # 모델이 한 번에 요청한 함수 호출을 순서대로 실행합니다.
            for call in function_calls:
                # JSON 파싱 실패 시 추적에 남길 원본 인수를 먼저 준비합니다.
                arguments: dict = {"raw": call.arguments}

                try:
                    # JSON 문자열 인수를 Python 딕셔너리로 변환합니다.
                    arguments = json.loads(call.arguments or "{}")
                    if not isinstance(arguments, dict):
                        raise ValueError("Tool 인수는 JSON 객체여야 합니다.")

                    # MCP Client를 통해 실제 MCP Tool을 호출합니다.
                    result = await self.mcp_client.call_tool(call.name, arguments)
                except Exception as exc:
                    # Tool 오류도 모델에 전달하여 사실대로 설명하거나 복구할 수 있게 합니다.
                    result = {"is_error": True, "error": str(exc)}

                # 실행 라운드와 Tool 결과를 API 응답 추적 정보에 저장합니다.
                tool_trace.append(
                    {
                        "round": round_number,
                        "tool": call.name,
                        "arguments": arguments,
                        "result": result,
                    }
                )

                # OpenAI가 해석할 수 있도록 Tool 결과를 JSON 문자열로 전달합니다.
                tool_outputs.append(
                    {
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "output": json.dumps(result, ensure_ascii=False),
                    }
                )

            # 최대 라운드에 도달하면 추가 Tool 호출 없이 결과를 요약하게 합니다.
            reached_limit = round_number == self.settings.openai_max_tool_rounds
            response = await self.openai.responses.create(
                model=self.settings.openai_model,
                instructions=self.INSTRUCTIONS,
                previous_response_id=response.id,
                input=tool_outputs,
                tools=tools,
                tool_choice="none" if reached_limit else "auto",
            )

            # 제한 때문에 Tool 사용을 중단한 경우 현재 결과로 최종 답변을 반환합니다.
            if reached_limit:
                return {
                    "mode": "openai",
                    "model": self.settings.openai_model,
                    "answer": response.output_text,
                    "tool_rounds": round_number,
                    "tool_limit_reached": True,
                    "tool_trace": tool_trace,
                }

        # 설정상 최소 한 라운드는 보장되므로 도달하지 않는 방어 코드입니다.
        raise RuntimeError("OpenAI Tool 실행 루프가 비정상적으로 종료되었습니다.")
