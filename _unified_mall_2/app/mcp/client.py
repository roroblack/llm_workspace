"""MCP 클라이언트 서비스 — stdio로 우리 MCP 서버에 연결해 목록/호출을 시연.

앱(FastAPI)이 MCP 클라이언트가 되어, 별도 프로세스로 `python -m app.mcp.server`를
띄우고 stdio로 통신한다. "요청마다 서버 subprocess 기동"은 **학습용 시연**이며 운영
구조가 아니다(운영은 장수명 서버·풀 등 별도 설계).

폴백 없음: 서버 기동/통신 실패는 예외로 전파한다.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import re
import secrets

from app.core.errors import (
    AppError,
    ConfigError,
    InfraError,
    LLMOutputError,
    ValidationErr,
)

# 서버가 '[APPERR:<nonce>:<code>]'로 실어 보낸 도구 내부 AppError의 error_code → 타입 복원표.
_APPERR_BY_CODE: dict[str, type[AppError]] = {
    ValidationErr.error_code: ValidationErr,
    ConfigError.error_code: ConfigError,
    InfraError.error_code: InfraError,
    LLMOutputError.error_code: LLMOutputError,
}
# FastMCP의 인자 검증 오류 고유 형태: "N validation error(s) for <Tool>Arguments".
# 이 시그니처만 프레임워크 인자 오류로 인정한다(도구 내부 메시지에 우연히 'validation error'가
# 섞여도 422로 오분류하지 않도록 정밀화).
_ARG_VALIDATION_RE = re.compile(r"\d+ validation error[s]? for \w+Arguments")


def _new_nonce() -> str:
    """호출마다 새로 발급하는 1회용 비밀. 서버 서브프로세스에 env로 넘긴다."""
    return secrets.token_hex(16)


def _apperr_marker_re(nonce: str) -> re.Pattern[str]:
    """이번 호출의 정확한 nonce를 가진 마커만 신뢰하는 정규식."""
    return re.compile(
        rf"^Error executing tool \S+: \[APPERR:{re.escape(nonce)}:(\w+)\]\s*(.*)", re.S
    )

# app/mcp/client.py → parents[2] = 프로젝트 루트(= app 패키지의 부모)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _unwrap(exc: BaseException) -> BaseException:
    """anyio TaskGroup이 예외를 (Base)ExceptionGroup으로 감쌀 수 있어 최내부 예외를 꺼낸다."""
    while isinstance(exc, BaseExceptionGroup) and exc.exceptions:
        exc = exc.exceptions[0]
    return exc


def _normalize(exc: BaseException, name: str) -> BaseException:
    """전송/프로토콜 예외를 타입 있는 AppError로 승격한다(폴백 아님, 명시적 실패).

    - 내부에서 이미 올린 AppError(isError→분류된 오류 등)는 그대로 통과.
    - 그 밖의 전송/연결 오류는 InfraError(503)로 승격 — 실패를 200 성공으로 감추지 않는다.
    """
    leaf = _unwrap(exc)
    if isinstance(leaf, AppError):
        return leaf
    return InfraError(f"MCP 통신/도구 오류: {name}: {type(leaf).__name__}: {leaf}")


def _tool_error(name: str, detail: str, nonce: str) -> AppError:
    """FastMCP가 isError=True로 돌려준 도구 오류를 원인별 타입으로 복원한다.

    우선순위:
    1. 서버가 **이번 호출의 정확한 nonce로** 실은 '[APPERR:<nonce>:<code>]' 마커 → 원래 AppError
       타입 복원. nonce는 호출마다 새로 발급되는 1회용 비밀이라, 호출자가 도구명/인자에 마커를
       심거나 지난 호출의 nonce를 재사용해도 위조 불가(주입 방지).
    2. FastMCP 프레임워크 오류: 존재하지 않는 도구·pydantic 인자 검증(고유 시그니처) → ValidationErr(422).
    3. 그 밖의 실행 실패(SQLAlchemy 등 비-AppError, 위조 마커 포함) → InfraError(503).
    프로토콜 경계를 넘으면 예외 타입이 사라지므로 메시지로 복원한다.
    """
    m = _apperr_marker_re(nonce).search(detail)
    if m:
        code, message = m.group(1), m.group(2).strip()
        cls = _APPERR_BY_CODE.get(code, InfraError)
        return cls(f"MCP 도구 '{name}': {message}")

    is_user_error = detail.startswith("Unknown tool") or bool(_ARG_VALIDATION_RE.search(detail))
    if is_user_error:
        return ValidationErr(f"MCP 도구 호출 오류(이름/인자): {name}: {detail}")
    return InfraError(f"MCP 도구 실행 실패: {name}: {detail}")


def _server_params(nonce: str | None = None) -> StdioServerParameters:
    """우리 MCP 서버를 stdio 서브프로세스로 띄우기 위한 파라미터.

    - command: 현재 파이썬 인터프리터(동일 venv 보장)
    - args: `-m app.mcp.server`
    - cwd/env: 프로젝트 루트에서 실행 + PYTHONPATH로 app 패키지 임포트 보장
    - nonce: 이번 호출용 1회용 비밀. 서버가 도구 내부 AppError를 위조 불가하게 표식하는 데 쓴다.
    """
    env = dict(os.environ)
    existing = env.get("PYTHONPATH", "")
    root = str(_PROJECT_ROOT)
    env["PYTHONPATH"] = root + (os.pathsep + existing if existing else "")
    if nonce is not None:
        env["MCP_APPERR_NONCE"] = nonce
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.mcp.server"],
        cwd=root,
        env=env,
    )


async def list_tools() -> list[dict[str, Any]]:
    """서버가 노출한 도구 목록(name/description/input schema)을 반환한다."""
    try:
        async with stdio_client(_server_params()) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                resp = await session.list_tools()
                return [
                    {
                        "name": t.name,
                        "description": t.description,
                        "input_schema": t.inputSchema,
                    }
                    for t in resp.tools
                ]
    except Exception as e:  # 전송/프로토콜 실패 → 타입 있는 오류로 승격(폴백 아님)
        raise _normalize(e, "list_tools") from e


async def call_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    """도구를 호출하고 구조화 결과(structuredContent 우선)를 반환한다.

    구분(폴백 금지, RULE 3.2):
    - **비즈니스 실패**(없는 상품/주문 등)는 도구가 {"ok": false, ...} 구조화 결과로
      반환하며 `isError=False`다 → 정상 결과로 그대로 돌려준다(HTTP 200).
    - **도구 오류**(`isError=True`)는 200 성공 봉투로 감싸지 않고 원인별로 승격한다:
      존재하지 않는 도구·인자 검증 실패 → `ValidationErr`(422), 실제 실행 실패(DB 미준비
      등) → `InfraError`(503). (`_tool_error` 참고)
    - **전송/연결 오류**는 `InfraError`(503). anyio가 ExceptionGroup으로 감싸면 언랩한다.
    """
    nonce = _new_nonce()  # 이번 호출 전용 1회용 비밀(재사용·stdout 관찰 시에도 다음 호출 무영향)
    try:
        async with stdio_client(_server_params(nonce)) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(name, arguments or {})
                text_blocks = [
                    getattr(block, "text", None)
                    for block in getattr(result, "content", [])
                    if getattr(block, "type", None) == "text"
                ]
                text = [t for t in text_blocks if t is not None]
                if getattr(result, "isError", False):
                    detail = " ".join(text) or "알 수 없는 MCP 도구 오류"
                    raise _tool_error(name, detail, nonce)
                # FastMCP는 dict 반환 도구를 structuredContent로 함께 실어준다.
                return {
                    "structured": getattr(result, "structuredContent", None),
                    "text": text,
                }
    except Exception as e:
        raise _normalize(e, name) from e
