# Function Calling 콘솔 실습 프로젝트


## 1. 프로젝트 구성

```text
function_calling_console_project/
├─ code/
│  ├─ common.py                 # 제공된 공통 모듈
│  ├─ main.py                   # 콘솔 앱 시작 파일
│  ├─ tools.py                  # 재고/환율 도구 함수 + Torch 통계
│  ├─ gemini_app.py             # Gemini Function Calling 예제
│  └─ openai_app.py             # OpenAI Tool Calling 예제
├─ data/
│  ├─ inventory.csv             # 재고 샘플 데이터
│  └─ exchange_rates.csv        # 환율 샘플 데이터              
├─ .env.example                 # 환경변수 예시
├─ requirements.txt             # 설치 패키지 목록
├─ .gitignore
└─ README.md
```

## 2. PyCharm 실행 순서

1. PyCharm에서 `function_calling_console_project` 폴더를 엽니다.
2. Python Interpreter를 설정합니다.
3. 터미널에서 패키지를 설치합니다.

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

4. `.env.example`을 복사해서 `.env` 파일을 만듭니다.

```bash
copy .env.example .env
```

5. `.env` 파일에 API 키를 입력합니다.

```text
GOOGLE_API_KEY=본인_Google_API_Key
OPENAI_API_KEY=본인_OpenAI_API_Key
```

6. `code/main.py`를 실행합니다.

```bash
python code/main.py
```

## 3. 메뉴 설명

| 메뉴 | 기능 |
|---|---|
| 1 | 모델 없이 도구 함수 직접 테스트 |
| 2 | PyTorch 텐서로 재고 통계 계산 |
| 3 | Gemini 자동 Function Calling 실행 |
| 4 | Gemini 수동 루프 실행 |
| 5 | Gemini 도구 오류 처리 실행 |
| 6 | OpenAI Tool Calling 실행 |

## 4. 학습 핵심

- LLM은 함수를 직접 실행하지 않고, 어떤 함수를 어떤 인자로 호출할지 결정합니다.
- 실제 실행은 파이썬 코드 또는 SDK가 담당합니다.
- 자동 Function Calling은 편하지만 중간 과정이 잘 보이지 않습니다.
- 수동 루프는 모델의 결정, 함수 실행, 결과 전달 과정을 직접 확인할 수 있습니다.
- 도구 함수는 `try/except`로 오류를 친절한 문자열로 바꾸어야 에이전트가 멈추지 않습니다.
