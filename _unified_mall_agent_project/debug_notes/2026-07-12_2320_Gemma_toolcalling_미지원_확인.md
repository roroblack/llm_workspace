# 디버그 노트 — 로컬 Gemma의 OpenAI tool-calling 미지원 확인

- 일시: 2026-07-12 23:20
- 맥락: Phase 3 ReAct 에이전트 라이브 스모크

## 발견
로컬 Gemma(llama-cpp OpenAI 호환 서버)에 `tools=TOOLS_SCHEMA`로 요청하면,
Gemma는 **네이티브 `tool_calls`를 반환하지 않는다.** 대신 `content`에 유사 tool-call
텍스트를 뱉는다:
```
answer: '<|tool_call>call:get_price{product_code:<|"|>P0001<|"|>}<tool_call|>'
stopped_by: final_answer
steps: []
```
llama-cpp의 OpenAI 어댑터가 이 텍스트를 구조화 `tool_calls`로 파싱하지 못해,
ReAct 루프는 이를 최종답변(text)으로 처리한다. → **로컬 Gemma로는 도구 실제 호출이 안 됨.**

## 판단 (RULE 정합)
- ReAct **루프 로직 자체는 mock chat_fn 결정론적 테스트 5종으로 검증됨**(도구실행·관찰·중복차단·max_steps·bad_args·unknown_tool). 이게 Phase 3의 필수 DoD.
- 유사 tool-call 텍스트를 정규식으로 파싱하는 폴백은 **매우 취약**(Gemma 특유 포맷 `<|tool_call>...`)하므로 RULE 3.3(YAGNI·취약코드 금지)에 따라 **추가하지 않음.**
- **라이브 tool-calling 검증은 최종 실키 스모크(OpenAI/Gemini)로 이관.** OpenAI/Gemini는 네이티브 tool-calling 지원.

## 로컬 Gemma의 유효 범위 (빌드 중 활용)
- ✅ 유효: 일반 completion(프롬프트 응답·요약·분류·RAG 답변생성 등) — Phase 4/5/7의 비-tool 부분
- ❌ 불가: OpenAI 네이티브 tool-calling(ReAct 도구 실행) — mock으로 검증, 최종 실키로 라이브 확인

## 영향
- Phase 3.5(LangChain): LangChain의 tool-calling도 로컬 Gemma에선 동일 제약 예상 → mock/구조 검증 위주, 라이브는 실키.
- Phase 4/5/7: 로컬 Gemma로 라이브 검증 가능(일반 completion).
