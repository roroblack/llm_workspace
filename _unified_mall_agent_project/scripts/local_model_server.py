"""로컬 Gemma OpenAI 호환 서버 (개발용).

llama_cpp.server는 starlette_context(starlette 1.x)를 요구해 앱의 fastapi(starlette
0.47)와 충돌한다. 이를 피하기 위해 llama_cpp.Llama를 직접 감싼 최소 OpenAI 호환
엔드포인트를 제공한다. create_chat_completion이 이미 OpenAI 형식을 반환하므로
얇은 패스스루로 충분하다.

실행:
    python scripts/local_model_server.py

환경변수:
    GEMMA_GGUF_PATH  : GGUF 모델 경로 (기본: HF 캐시 경로)
    LOCAL_MODEL_PORT : 포트 (기본 8000)
    N_CTX            : 컨텍스트 (기본 4096)
"""

from __future__ import annotations

import os

import uvicorn
from fastapi import FastAPI, Request
from llama_cpp import Llama

DEFAULT_GGUF = (
    r"C:\Users\playdata2\.cache\huggingface\hub"
    r"\models--google--gemma-4-E4B-it-qat-q4_0-gguf\snapshots"
    r"\bb3b92e6f031fa438b409f898dd9f14f499a0cb0\gemma-4-E4B_q4_0-it.gguf"
)

GGUF_PATH = os.environ.get("GEMMA_GGUF_PATH", DEFAULT_GGUF)
PORT = int(os.environ.get("LOCAL_MODEL_PORT", "8000"))
# 이 머신은 여유 RAM이 ~5GB로 빠듯하다. 컴퓨트 버퍼는 배치에 비례하므로 작게 잡는다
# (debug_notes 2026-07-12_2028 / RAM 제약 노트 참조).
N_CTX = int(os.environ.get("N_CTX", "1024"))
N_BATCH = int(os.environ.get("N_BATCH", "32"))

app = FastAPI(title="Local Gemma (OpenAI-compatible)")
_llm: Llama | None = None


def get_llm() -> Llama:
    global _llm
    if _llm is None:
        _llm = Llama(
            model_path=GGUF_PATH,
            n_ctx=N_CTX,
            n_batch=N_BATCH,
            n_ubatch=N_BATCH,
            use_mmap=True,
            verbose=False,
        )
    return _llm


@app.get("/v1/models")
def list_models() -> dict:
    return {"object": "list", "data": [{"id": "gemma-4-e4b", "object": "model"}]}


@app.post("/v1/chat/completions")
async def chat_completions(request: Request) -> dict:
    body = await request.json()
    llm = get_llm()
    # tool calling 포함 OpenAI 파라미터를 그대로 전달
    kwargs = {"messages": body["messages"]}
    for key in ("temperature", "max_tokens", "top_p", "tools", "tool_choice", "stop"):
        if key in body and body[key] is not None:
            kwargs[key] = body[key]
    return llm.create_chat_completion(**kwargs)


if __name__ == "__main__":
    print(f"[local_model_server] loading {GGUF_PATH}")
    get_llm()
    print(f"[local_model_server] ready on http://127.0.0.1:{PORT}/v1")
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")
