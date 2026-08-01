# LangGraph AI Team PyCharm 콘솔 프로젝트


## 실행 메뉴

- 경쟁사 CSV 데이터 로드
- Researcher 단일 노드
- Analyst 단일 노드
- Writer 단일 노드
- Researcher → Analyst → Writer 기본 StateGraph
- `check → redo/ok` 조건부 품질 재검토
- `reports/` 중간 산출물 저장
- 실습문제 1: Reviewer → Finalize 노드 추가
- 실습문제 2: 네 단계 결과를 `output/`에 저장

HTML 설명을 요약하거나 표시하는 메뉴는 포함하지 않았습니다.

## 프로젝트 구조

```text
ai_team_console_project/
├── main.py
├── code/
│   └── common.py                 # 제공된 공통 모듈 원본
├── code_app/
│   ├── common_bridge.py
│   ├── ai_team.py
│   ├── conditional_review.py
│   ├── artifact_save.py
│   ├── exercise_reviewer.py
│   ├── exercise_save_all.py
│   └── console_menu.py
├── data/                         # 제공된 data.zip 내용
├── reports/                      # 타임스탬프 중간 산출물
├── output/                       # 실습문제 2 고정 파일 4개
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

## PyCharm 실행 순서

1. 압축을 해제하고 PyCharm에서 프로젝트 루트 폴더를 엽니다.
2. Python 3.11 가상환경을 생성합니다.
3. PyCharm Terminal에서 다음 명령을 실행합니다.

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

4. `.env.example`을 복사해 `.env`를 만듭니다.

Windows 명령 프롬프트:

```bat
copy .env.example .env
```

PowerShell:

```powershell
Copy-Item .env.example .env
```

5. `.env`에 실제 OpenAI 및 Gemini API 키를 입력합니다.
6. `main.py`를 우클릭해 **Run 'main'** 을 실행합니다.
7. 먼저 OpenAI 또는 Gemini를 선택하고 하위 실습 메뉴를 실행합니다.

## 테스트

테스트는 실제 LLM API를 호출하지 않습니다.

```bash
pytest -q
```

## common.py 유지 방식

제공된 `common.py`는 `code/common.py`에 수정 없이 복사했습니다. 애플리케이션 코드는 `code_app/common_bridge.py`를 통해 이 원본 모듈의 `get_chat`, `DATA`, `ROOT`를 사용합니다. 따라서 OpenAI는 `get_chat(provider="openai")`, Gemini는 `get_chat(provider="gemini")` 방식으로 동일한 공통 모듈을 사용합니다.

## 참고

- 단일 노드 메뉴도 해당 단계가 요구하는 앞 단계 산출물을 자동으로 준비합니다.
- `stream()`과 `invoke()`를 연속 호출하지 않으므로 같은 그래프가 중복 실행되지 않습니다.
- 조건부 그래프는 `MAX_RETRIES = 2`로 무한 반복을 방지합니다.
- API 오류는 콘솔 메뉴에서 잡아 프로그램 전체가 종료되지 않도록 처리합니다.
