# CoT Reasoning Prompt 콘솔 실습 앱

## 1. 프로젝트 구조

```text
cot_console_project/
├─ .env.example
├─ .gitignore
├─ README.md
├─ requirements.txt
├─ data/
│  ├─ math_word_problems.csv
│  └─ docs/
└─ src/
   ├─ common.py
   ├─ llm_clients.py
   ├─ main.py
   └─ torch_metrics.py
```

## 2. PyCharm 실행 순서

1. PyCharm에서 `cot_console_project` 폴더를 엽니다.
2. Python Interpreter를 설정합니다.
3. 터미널에서 패키지를 설치합니다.

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

4. `.env.example` 파일을 복사해서 `.env` 파일을 만듭니다.

```bash
copy .env.example .env
```

macOS/Linux에서는 다음 명령을 사용합니다.

```bash
cp .env.example .env
```

5. `.env` 파일에 본인의 API 키를 입력합니다.

```env
GOOGLE_API_KEY=본인_Gemini_API_KEY
OPENAI_API_KEY=본인_OpenAI_API_KEY
GEMINI_MODEL=gemini-2.5-flash
OPENAI_MODEL=gpt-4o-mini
```

6. 다음 파일을 실행합니다.

```bash
python src/main.py
```

## 3. 메뉴 설명

```text
1. 프로젝트/공통 모듈 정보 확인
2. Torch 기반 정답률 비교 실행(API 키 불필요)
3. Gemini API 직접 답변 + CoT + 자기검증 실행
4. OpenAI API 직접 답변 + CoT + 자기검증 실행
0. 종료
```

## 4. 핵심 학습 내용

- 직접 답변은 빠르지만 다단계 계산에서 틀릴 수 있습니다.
- CoT는 단계적으로 풀이를 작성하게 하여 정답률을 높입니다.
- 자기검증은 CoT 풀이를 다시 검산하여 신뢰도를 높입니다.
- 단순 질문에는 CoT가 토큰 낭비가 될 수 있습니다.
- Torch Tensor를 사용하면 정답률 계산 과정을 명확하게 확인할 수 있습니다.


Gemini/OpenAI 메뉴는 `.env`에 API 키를 입력한 뒤 실행합니다.
