# Agent Loop 콘솔 실습 프로젝트


## 1. 프로젝트 구성

```text
agent_loop_basic_console_project/
├─ main.py
├─ requirements.txt
├─ .env.example
├─ .gitignore
├─ README.md
├─ code/
│  ├─ common.py
│  ├─ data_tools.py
│  ├─ torch_inventory.py
│  ├─ local_agent_loop.py
│  ├─ gemini_agent_loop.py
│  └─ openai_agent_loop.py
└─ data/
   ├─ inventory.csv

```

## 2. PyCharm 실행 방법

1. PyCharm에서 `agent_loop_basic_console_project` 폴더를 엽니다.
2. Python Interpreter를 설정합니다.
3. 터미널에서 패키지를 설치합니다.

```bash
pip install -r requirements.txt
```

4. `.env.example` 파일을 복사해서 `.env` 파일을 만듭니다.

```bash
copy .env.example .env
```

5. `.env`에 API 키를 입력합니다.

```env
GOOGLE_API_KEY=본인_Google_API_Key
OPENAI_API_KEY=본인_OpenAI_API_Key
GEMINI_MODEL=gemini-2.5-flash
OPENAI_MODEL=gpt-4o-mini
```

6. PyCharm에서 `main.py`를 실행합니다.

## 3. 메뉴 설명

```text
1. common.py 공통 모듈 상태 확인
2. Torch 재고/재주문 기준 분석
3. API 없이 로컬 Agent Loop 실행
4. Gemini API Agent Loop 실행
5. OpenAI API Agent Loop 실행
0. 종료
```

## 4. 학습 포인트

- `common.py`에서 `.env` API 키와 `data/` 경로를 공통 관리합니다.
- `torch` 텐서 연산으로 재고와 재주문 기준을 비교합니다.
- Agent Loop의 핵심인 `질문 → 도구 호출 → 관찰 → 다음 행동` 반복을 확인합니다.
- `max_steps`, 중복 호출 방지, history 트리밍 구조를 코드로 확인합니다.
- Gemini API와 OpenAI API 방식의 tool/function calling 루프를 각각 확인합니다.


Gemini/OpenAI 메뉴는 `.env`에 키를 입력해야 정상 호출됩니다.
