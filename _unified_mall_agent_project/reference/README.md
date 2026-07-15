# reference/ — 복습 레퍼런스 (증발한 날것 패턴 보존)

통합 프로젝트(`app/`)는 여러 강의의 학습을 **깔끔한 추상화**로 통합했다. 그 과정에서
"ChatGPT API가 실제로 어떻게 동작하는가" 같은 **날것의 세부 지식이 코드 표면에서 사라진다.**
예: `app/core/llm_clients.py`는 `OpenAI(...)` 한 줄로 감싸버려서, gpt-5/o 계열의
파라미터 분기·`max_completion_tokens`·`reasoning_effort`·`finish_reason` 같은
**복습 가치가 큰 디테일이 안 보인다.**

이 폴더는 그 **날것 패턴을 개념별로 최소·주석·실행가능 예제로 보존**한다.
통합 앱은 "작동하는 통합", 공략집은 "개념 설명", 이 reference는 **"실제 코드로 복습"**을 담당한다.

> 이 코드들은 **학습·복습용 참조**다. 실제 API 호출은 키가 필요하며(각 파일 상단 표기),
> 통합 앱(`app/`)과 분리돼 있다(프로덕션 경로 아님). 원본 출처를 각 파일에 인용한다.
>
> ⚠️ **정확성 주의**: LLM API는 빠르게 바뀐다. 여기 담긴 모델 지원 범위·파라미터(예:
> `max_tokens`는 deprecated→`max_completion_tokens`)·정책값(REASONING_MIN_TOKENS 등)은
> **작성 시점·특정 프로젝트 휴리스틱**이 섞여 있다. 각 파일 주석의 "정확성 주의"를 함께 볼 것.
> '보존해야 할 날것 지식'과 '그때의 프로젝트 선택'을 구분해서 읽자.

## 목차 (개념 → 파일 → 원본 → 공략집 스테이지)

| # | 개념 | 파일 | 원본 프로젝트 | 스테이지 |
|---|---|---|---|---|
| 01 | **OpenAI Chat Completions 날것** (gpt-5/o 파라미터 분기) | `01_openai_chat_completions_raw.py` | chatgpt_chatbot_project | 6·7 |
| 02 | **OpenAI Responses API** (신형, reasoning) | `02_openai_responses_api.py` | openai_music_recommend_chatbot | 6 |
| 03 | **Gemini 날것 SDK** (google-genai) | `03_gemini_genai_raw.py` | fastapi_llm_parameter_test | 6 |
| 04 | **프롬프트 엔지니어링** (few-shot·JSON강제 3방식·인젝션방어) | `04_prompt_engineering.py` | prompt_console_project | 8 |
| 05 | **CoT·자기검증** | `05_cot_self_verify.py` | cot_console_project | 9 |
| 06 | **Function Calling** (자동 vs 수동, tool_choice) | `06_function_calling_manual.py` | function_calling_console_project | 10 |
| 07 | **RAG 날것** (청킹→임베딩→FAISS, 인덱싱/서비스 분리) | `07_rag_faiss_raw.py` | vector_db_pycharm_project | 12 |

### 통합 앱에 이미 잘 반영돼 별도 복습 불필요 (또는 레거시 폴더에서)
- 형태소 전처리(스테이지1): `test_konlpy_project`, `konlpy_practice_project`
- 워드임베딩 BOW/TF-IDF(2): `word_embed_project`
- LSTM/CNN 분류(3): `nlp_model_project`, `BBC_RNN_Classifier_project`
- BERT 파인튜닝(4): `Bert_sentiment_project` → 통합 `app/ml/sentiment.py`가 실모델 재사용
- Transformer/GPT(5): `smart_translator_project`, `kogpt2_streamlit_chatbot_project`

## ★ 이 폴더가 필요한 이유 — 실제 사례
통합 포팅 때 `app/agent/react.py`가 `tool_choice="auto"`를 **빠뜨렸다.** 그런데 원본
`function_calling_console_project/code/openai_app.py`에는 그게 **처음부터 있었다.**
즉 교재가 가르친 디테일이 통합 추상화에서 증발했고, 나중에 "버그"로 다시 잡았다
(`debug_notes/2026-07-13_2130_*`). **날것 레퍼런스가 있으면 이런 손실을 막는다.**

## 실행
```bash
# 개념 복습(읽기): 파일을 그냥 연다
# 실제 실행(선택): .env에 OPENAI_API_KEY 또는 GOOGLE_API_KEY 설정 후
python reference/01_openai_chat_completions_raw.py
```
