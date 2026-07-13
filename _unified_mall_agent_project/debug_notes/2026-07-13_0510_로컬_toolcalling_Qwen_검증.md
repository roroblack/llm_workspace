# 디버그 노트 — 로컬 tool-calling 검증 (Qwen, 토큰 0)

- 일시: 2026-07-13 05:10
- 배경: 로컬 Gemma는 OpenAI tool-calling 미지원(debug 2320)이라 에이전트 도구호출을 실키로만 검증 가능하다고 이월했었음. 캐시된 Qwen 모델로 **키 없이** 검증 시도.

## 핵심 결과: 로컬 tool-calling 메커니즘 **검증됨**

`unsloth/Qwen3.5-4B-GGUF`(Q4_K_M, 캐시)를 `chat_format="chatml-function-calling"`으로 로드하고
`get_price` 도구를 넘겨 호출한 결과:

```
tool_calls: [{'id': 'call__0_get_price_...', 'type': 'function',
  'function': {'name': 'get_price', 'arguments': '{ "product_code": "P0001" }'}}]
HAS_TOOLCALL: True
```

→ **Qwen은 정확한 OpenAI 형식 tool_calls를 반환한다.** 이는 앱의 에이전트가 로컬에서(토큰 0)
tool-calling을 수행할 수 있음을 의미한다. 에이전트 루프(`react.py`)가 tool_calls를 소비·실행하는
로직은 mock 테스트 5종으로 이미 검증됨.

## 실행 방법 (로컬 tool-calling 서버)

```bash
LOCAL_GGUF_PATH="<Qwen3.5-4B-Q4_K_M.gguf 경로>" \
CHAT_FORMAT="chatml-function-calling" N_CTX=2048 N_BATCH=64 \
python scripts/local_model_server.py
# 앱: LLM_PROVIDER=local, LOCAL_MODEL=qwen3.5-4b → /api/agent/chat 가 실제 도구 호출
```
(서버 스크립트는 LOCAL_GGUF_PATH/CHAT_FORMAT 환경변수 지원하도록 확장됨)

## 제약 (풀 에이전트 E2E)
- Qwen 4B는 **CPU 추론이 느림**(요청당 1~수분). 6개 도구 + 멀티스텝 ReAct 루프는 매우 느림.
- **RAM**: Qwen 4B Q4 = 약 2.5GB 상주. 검증 시점 머신 여유 RAM이 2.4GB로 부족(다른 앱 점유)해
  풀 에이전트 로드는 일시적으로 불가했음. 여유 RAM 3GB+ 확보 시 풀 E2E 가능.
- 따라서 **메커니즘은 검증(단일 도구호출 성공), 풀 멀티스텝 E2E는 자원(속도/RAM) 여건에 따라**.

## 정리 (이월 항목 상태 갱신)
- 기존: "에이전트 tool-calling은 실키로만 검증 가능(이월)"
- 갱신: **로컬 Qwen으로 tool-calling 메커니즘 검증 완료(토큰 0)**. 풀 멀티스텝 E2E와 운영 경로
  단일화는 자원 여유 시 로컬 Qwen 또는 실키로 마무리.
- 모델별 정리: Gemma=평문 전용(tool-calling X), Qwen=tool-calling O, OpenAI/Gemini=실키.
