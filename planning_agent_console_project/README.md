# Planning Agent 콘솔 실습 프로젝트

제공된 `common.py`를 공통 모듈로 사용하고, 제8강 HTML 자료의 코드와 설명을 콘솔에서 확인할 수 있도록 만든 PyCharm용 기본 Python 프로젝트입니다.

## 실행 방법

```bash
cd planning_agent_console_project
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
copy .env.example .env
python code/main.py
```

`.env`에 `GOOGLE_API_KEY`, `OPENAI_API_KEY`를 입력하면 Gemini/OpenAI API 실습을 실행할 수 있습니다. 키가 없어도 HTML 확인, Torch 집계, 규칙 기반 예시 계획은 실행됩니다.

## 주요 메뉴

- HTML 설명 요약 보기
- HTML 코드 블록 보기
- PyTorch 프로젝트 작업 상태 집계
- Gemini Planner 실행
- Gemini 계획 검증 및 재계획
- OpenAI Planner 실행
- OpenAI 계획 검증 및 재계획

## 프로젝트 구조

```text
planning_agent_console_project/
├─ code/
│  ├─ common.py
│  ├─ main.py
│  ├─ html_reader.py
│  ├─ torch_demo.py
│  ├─ planning_core.py
│  ├─ gemini_app.py
│  └─ openai_app.py
├─ data/
│  ├─ project_tasks.csv
│  └─ sample_goals.txt
├─ docs/
│  └─ 제공 HTML 파일들
├─ .env.example
├─ requirements.txt
├─ .gitignore
└─ README.md
```

## 학습 내용

이 프로젝트는 다음 내용을 확인합니다.

- 큰 목표를 하위 작업으로 분해하는 Planning Agent 구조
- Plan-and-Execute 방식
- ReAct와 Plan-and-Execute 차이
- Pydantic 기반 구조화 출력
- 계획 검증과 재계획 패턴
- PyTorch 텐서 기반 상태 집계
