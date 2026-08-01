# Planner / Worker Role Agent 콘솔 프로젝트


## 포함 기능

1. 환경변수와 캠페인 CSV 확인
2. Planner 구조화 출력으로 하위 작업 분해
3. Worker 단일 작업 실행
4. Planner → Worker → 결과 취합
5. Worker 오류 재시도, 스킵, 부분 실패 기록
6. 실습문제 1 완성: Reviewer 단계 추가
7. 실습문제 2 완성: 역할 프롬프트 YAML 외부화

## 프로젝트 구조

```text
planner_worker_console_project/
├── main.py
├── app/
│   ├── common.py
│   ├── console_app.py
│   ├── role_agent.py
│   ├── retry_agent.py
│   ├── reviewer_exercise.py
│   └── yaml_exercise.py
├── data/
│   ├── marketing_brief.csv
│   ├── role_prompts.yaml
│   └── 제공된 기타 데이터 파일
├── tests/test_project.py
├── .env.example
├── requirements.txt
└── README.md
```

## PyCharm 실행 순서

1. 압축을 풀고 PyCharm에서 프로젝트 루트 폴더를 엽니다.
2. Python 3.11 가상환경을 생성합니다.
3. PyCharm Terminal에서 다음 명령을 실행합니다.

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

4. `.env.example`을 복사해 `.env`를 만들고 실제 API 키를 입력합니다.

```env
OPENAI_API_KEY=실제_OpenAI_API_KEY
OPENAI_MODEL=gpt-4o-mini
GOOGLE_API_KEY=실제_Google_API_KEY
GEMINI_MODEL=gemini-2.5-flash
```

5. `main.py`를 마우스 오른쪽 버튼으로 클릭하고 **Run 'main'** 을 선택합니다.
6. 먼저 OpenAI 또는 Gemini를 선택한 다음 원하는 하위 실습을 실행합니다.

## 터미널 실행

```bash
python main.py
```

## API 호출 없는 기본 검증

```bash
python -m pytest -q
```

## 참고

- 메뉴 5는 재시도 동작을 확실히 보여주기 위해 두 번째 Worker 작업에 `TimeoutError`를 의도적으로 발생시킵니다. 나머지 작업은 계속 실행됩니다.
- API 키, 요금제, 모델 접근 권한, 호출량 제한에 따라 실제 LLM 호출 오류가 발생할 수 있습니다.
- 모델명이 계정에서 지원되지 않으면 `.env`의 `OPENAI_MODEL` 또는 `GEMINI_MODEL`만 변경하면 됩니다.
