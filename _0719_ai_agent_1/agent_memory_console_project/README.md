# Agent Memory Console Project

## 주요 기능

- OpenAI / Gemini 공급자 선택
- Stateless 호출 비교
- 수동 메시지 누적 방식
- `InMemorySaver` 기반 단기 기억
- `thread_id` 기반 세션 격리
- 긴 대화 트리밍
- 긴 대화 요약 압축
- `customers.csv`, `orders.csv`, `cs_inquiries.csv`, `user_profiles.json` 기반 기억형 고객 상담
- 자유 대화 메모리 테스트

## 프로젝트 구조

```text
agent_memory_console_project/
├── main.py
├── code/
│   ├── __init__.py
│   ├── common.py
│   ├── data_service.py
│   ├── memory_agent.py
│   └── message_utils.py
├── data/
│   ├── customers.csv
│   ├── orders.csv
│   ├── cs_inquiries.csv
│   ├── user_profiles.json
│   └── ...
├── .env.example
├── requirements.txt
├── .gitignore
└── README.md
```

## PyCharm 실행 순서

1. ZIP 파일을 원하는 폴더에 압축 해제합니다.
2. PyCharm에서 `agent_memory_console_project` 폴더를 엽니다.
3. Python 3.11 가상환경을 생성합니다.
4. PyCharm Terminal에서 다음 명령을 실행합니다.

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

5. `.env.example`을 복사하여 `.env` 파일을 만듭니다.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Windows CMD:

```cmd
copy .env.example .env
```

6. `.env`에 실제 API 키를 입력합니다.
7. `main.py`를 실행합니다.

```bash
python main.py
```

## 주의 사항

- `InMemorySaver`의 기억은 프로그램이 실행 중인 동안만 유지됩니다.
- 프로그램을 종료하면 인메모리 대화 기록은 사라집니다.
- OpenAI 메뉴는 `OPENAI_API_KEY`, Gemini 메뉴는 `GOOGLE_API_KEY`가 필요합니다.
- 공급자별 응답 형식 차이는 `message_utils.py`의 `message_to_text()`에서 처리합니다.
