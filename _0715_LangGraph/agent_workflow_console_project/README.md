# Agent Workflow Console Project

## 1. 구현 기능

- 제공된 `common.py` 방식의 `.env` 공통 설정
- Gemini API / OpenAI API 선택 실행
- PyTorch 텐서 기반 우선순위 점수 계산
- LangGraph `StateGraph`의 State / Node / Edge 실습
- 분류(LLM) → 우선순위(규칙) → 담당팀 배정(규칙)
- CSV 티켓 일괄 처리
- `add_conditional_edges` 기반 긴급 알림(`alert="즉시알림"`) 분기
- 빈 입력, 허용되지 않은 LLM 출력, 노드 예외 폴백
- 오류가 기록된 티켓의 `검토필요` 팀 최종 배정
- Gemini와 OpenAI 동일 입력 결과 비교
- 외부 API 호출이 없는 규칙 단위 테스트

## 2. 프로젝트 구조

```text
agent_workflow_console_project/
├── code/
│   ├── common.py
│   ├── main.py
│   ├── rules.py
│   ├── torch_demo.py
│   └── workflow.py
├── data/
│   └── support_tickets.csv
├── tests/
│   └── test_workflow_rules.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## 3. 권장 환경

- Windows 11
- PyCharm
- Python 3.11
- CPU 환경에서도 실행 가능

## 4. PyCharm에서 프로젝트 열기

1. 압축을 해제합니다.
2. PyCharm에서 **File → Open**을 선택합니다.
3. `agent_workflow_console_project` 폴더를 선택합니다.
4. **File → Settings → Project → Python Interpreter**로 이동합니다.
5. **Add Interpreter → Add Local Interpreter → Virtualenv**를 선택합니다.
6. Base interpreter로 Python 3.11을 선택하고 `.venv`를 생성합니다.

## 5. 패키지 설치

PyCharm 하단 Terminal에서 다음 명령을 실행합니다.

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

PyTorch 설치가 운영체제나 CUDA 환경 때문에 실패한다면 PyTorch 공식 설치 선택기에서 자신의 환경에 맞는 명령을 확인합니다.

## 6. API 키 설정

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

### Windows CMD

```cmd
copy .env.example .env
```

생성된 `.env` 파일에 실제 키를 입력합니다.

```env
GOOGLE_API_KEY=실제_Google_API_Key
GEMINI_MODEL=gemini-2.5-flash

OPENAI_API_KEY=실제_OpenAI_API_Key
OPENAI_MODEL=gpt-4o-mini
```

두 공급자를 모두 사용할 필요는 없습니다. 사용할 공급자의 키만 입력해도 해당 메뉴는 실행됩니다.

## 7. 실행 방법

### PyCharm 실행

1. `code/main.py`를 엽니다.
2. 편집기에서 마우스 오른쪽 버튼을 누릅니다.
3. **Run 'main'**을 선택합니다.

### 터미널 실행

프로젝트 루트에서 다음 명령을 실행합니다.

```bash
python code/main.py
```

## 8. 메뉴 구성

```text
1. 공통 환경 및 API 키 로드 상태 확인
2. LLM 공급자 선택 (Gemini / OpenAI)
3. PyTorch 기반 티켓 우선순위 점수 확인
4. 규칙 기반 노드 개별 실행
5. StateGraph 선형 워크플로우 단일 처리
6. CSV 티켓 알림 조건부 일괄 처리
7. add_conditional_edges 긴급 알림 조건부 분기
8. 노드 예외 처리와 검토필요 배정 검증
9. Gemini / OpenAI 결과 비교
0. 종료
```

HTML 페이지의 설명을 보여주는 메뉴는 포함하지 않았습니다.

## 9. 처리 흐름

### 선형 워크플로우

```text
START
  ↓
classify : LLM으로 카테고리 분류
  ↓
priority : 파이썬 규칙으로 우선순위 계산
  ↓
assign   : 카테고리-담당팀 규칙으로 배정
  ↓
END
```

### 조건부 워크플로우

```text
START → classify → priority
                      ├─ 긴급 → notify(alert="즉시알림") ┐
                      └─ 그 외 ───────────────────────────┴→ assign → END
```

`assign`은 모든 경로의 마지막 노드입니다. 앞선 노드에서 `error`가 기록된 경우
일반 담당팀 대신 `team="검토필요"`로 최종 배정합니다.

## 10. 테스트

외부 API 키 없이 규칙 로직을 테스트할 수 있습니다.

```bash
python -m pytest -q
```

테스트 항목:

- 정확한 카테고리 검증
- 설명 문장 안의 카테고리 추출
- 허용 범위 밖 결과의 `기타` 폴백
- 우선순위와 담당팀 규칙
- 조건부 라우터 경로
- 긴급 티켓에만 생성되는 `alert` 값
- 분류·우선순위·배정 예외의 상태 기록과 `검토필요` 배정

## 11. 주요 설계 보완

- LLM 응답은 공급자와 버전에 따라 `content`가 문자열 또는 콘텐츠 블록 목록일 수 있으므로 `message_to_text()`에서 안전하게 변환합니다.
- LLM 출력은 그대로 신뢰하지 않고 `CATEGORIES` 허용 목록으로 검증합니다.
- 빈 티켓은 API를 호출하지 않고 `기타`로 보정합니다.
- 각 노드는 `try/except`로 예외를 `error` 상태에 누적하고 다음 노드까지 계속 실행합니다.
- 조건부 그래프는 긴급 티켓만 `notify`를 거쳐 `alert="즉시알림"`을 남깁니다.
- 마지막 `assign` 노드는 오류가 하나라도 있으면 팀을 `검토필요`로 덮어씁니다.
- 우선순위와 담당팀 배정은 LLM이 필요하지 않으므로 결정적인 파이썬 규칙으로 처리합니다.

## 12. GitHub 업로드 예시

```bash
git init
git branch -M main
git add .
git commit -m "Complete agent workflow console project"
git remote add origin https://github.com/사용자명/저장소명.git
git push -u origin main
```

`.env` 파일은 `.gitignore`에 포함되어 있으므로 API 키가 GitHub에 올라가지 않습니다.
