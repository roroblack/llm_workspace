"""stdio MCP 서버의 공개 인터페이스를 검증합니다."""

from __future__ import annotations

import ast
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


PROJECT_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_TOOLS = {
    "add",
    "list_document_files",
    "read_document_file",
    "vector_search",
    "rebuild_rag_index",
    "rag_question_answer",
    "mysql_knowledge_list",
}
EXPECTED_RESOURCES = {"config://runtime", "docs://catalog"}
EXPECTED_PROMPTS = {"grounded_rag_prompt"}


def _parse_text_value(text: str):
    """JSON, Python 표현식, 일반 텍스트 순서로 Tool 텍스트를 해석합니다."""

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(text)
        except (SyntaxError, ValueError):
            return text


def tool_result_value(result, *, multiple: bool = False):
    """MCP SDK의 구조화 출력에서 원래 Python 반환값을 꺼냅니다."""

    structured_content = getattr(result, "structuredContent", None)
    if structured_content is not None:
        if set(structured_content) == {"result"}:
            return structured_content["result"]
        return structured_content

    # MCP 1.2 FastMCP는 list 항목을 여러 TextContent로 나누어 반환합니다.
    if multiple:
        return [_parse_text_value(item.text) for item in result.content]
    return _parse_text_value(result.content[0].text)


class McpServerProtocolTests(unittest.IsolatedAsyncioTestCase):
    """실제 자식 프로세스와 MCP stdio 프로토콜로 통신합니다."""

    async def test_server_contract_and_representative_calls(self) -> None:
        """README에 공개한 MCP 기능과 대표 응답을 검증합니다."""

        with tempfile.TemporaryDirectory() as faiss_dir:
            env = os.environ.copy()
            env.update(
                {
                    "EMBEDDING_BACKEND": "local",
                    "VECTOR_BACKEND": "faiss",
                    "FAISS_DIR": faiss_dir,
                    "MYSQL_ENABLED": "false",
                }
            )
            parameters = StdioServerParameters(
                command=sys.executable,
                args=["-m", "mcp_server.server"],
                env=env,
                cwd=PROJECT_ROOT,
            )

            async with stdio_client(parameters) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()

                    tools = await session.list_tools()
                    self.assertSetEqual({tool.name for tool in tools.tools}, EXPECTED_TOOLS)

                    resources = await session.list_resources()
                    self.assertSetEqual(
                        {str(resource.uri) for resource in resources.resources},
                        EXPECTED_RESOURCES,
                    )

                    prompts = await session.list_prompts()
                    self.assertSetEqual(
                        {prompt.name for prompt in prompts.prompts}, EXPECTED_PROMPTS
                    )

                    add_result = await session.call_tool("add", {"a": 1.25, "b": 2.75})
                    self.assertFalse(add_result.isError)
                    self.assertEqual(tool_result_value(add_result), 4.0)

                    files_result = await session.call_tool("list_document_files", {})
                    self.assertFalse(files_result.isError)
                    files = tool_result_value(files_result, multiple=True)
                    self.assertIn("mcp_overview.md", files)

                    read_result = await session.call_tool(
                        "read_document_file", {"filename": "mcp_overview.md"}
                    )
                    self.assertFalse(read_result.isError)
                    self.assertIn("Model Context Protocol", tool_result_value(read_result))

                    traversal_result = await session.call_tool(
                        "read_document_file", {"filename": "../README.md"}
                    )
                    self.assertTrue(traversal_result.isError)

                    config_result = await session.read_resource("config://runtime")
                    config = json.loads(config_result.contents[0].text)
                    self.assertEqual(config["embedding_backend"], "local")
                    self.assertNotIn("openai_api_key", config)

                    catalog_result = await session.read_resource("docs://catalog")
                    catalog = json.loads(catalog_result.contents[0].text)
                    self.assertIn("mcp_overview.md", catalog["files"])

                    prompt_result = await session.get_prompt(
                        "grounded_rag_prompt", {"question": "MCP의 구성은?"}
                    )
                    prompt_text = prompt_result.messages[0].content.text
                    self.assertIn("vector_search", prompt_text)
                    self.assertIn("MCP의 구성은?", prompt_text)

                    rebuild_result = await session.call_tool("rebuild_rag_index", {})
                    self.assertFalse(rebuild_result.isError)
                    rebuild_data = tool_result_value(rebuild_result)
                    self.assertGreater(rebuild_data["indexed_chunks"], 0)

                    search_result = await session.call_tool(
                        "vector_search", {"query": "MCP Tool Resource", "top_k": 1}
                    )
                    self.assertFalse(search_result.isError)
                    matches = tool_result_value(search_result, multiple=True)
                    self.assertEqual(len(matches), 1)
                    self.assertIn("source", matches[0])

                    rag_result = await session.call_tool(
                        "rag_question_answer",
                        {"question": "MCP의 주요 구성 요소는?", "top_k": 1},
                    )
                    self.assertFalse(rag_result.isError)
                    rag_data = tool_result_value(rag_result)
                    self.assertTrue(rag_data["sources"])
                    self.assertTrue(rag_data["matches"])

                    mysql_result = await session.call_tool("mysql_knowledge_list", {})
                    self.assertTrue(mysql_result.isError)


if __name__ == "__main__":
    unittest.main()
