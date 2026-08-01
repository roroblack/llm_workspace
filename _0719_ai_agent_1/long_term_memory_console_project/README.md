# OpenAI / Gemini Long-Term Memory 콘솔 프로젝트

제공된 `common.py`를 공통 모듈로 사용하고 `data.zip`의 고객·주문·상담·프로필 데이터를 활용하는 PyCharm 콘솔 앱입니다.

## 핵심 기능

- OpenAI / Gemini 공급자 선택
- 단기 기억과 장기 기억 비교
- JSON 프로필 조회 및 영속 갱신
- 장기 기억 도구를 사용하는 에이전트
- 새 에이전트와 새 세션에서도 프로필 유지 검증
- JSON 원본을 SQLite로 이관
- SQLite 행 단위 조회·갱신 및 SQL 인젝션 방어
- data.zip 고객·주문·상담 데이터 기반 개인화 응대
- 실습문제 해답 1, 2 실행 메뉴
- 실습 저장소 원본 복구 메뉴

## 프로젝트 구조

```text
long_term_memory_console_project/
├── main.py
├── code/
│   ├── common.py
│   ├── data_service.py
│   ├── long_term_agent.py
│   └── long_term_store.py
├── data/
│   ├── user_profiles.json       # 제공 원본, 직접 수정하지 않음
│   ├── user_profiles_rw.json    # 실행 중 자동 생성되는 JSON 장기 기억
│   ├── profiles.db              # 실행 중 자동 생성되는 SQLite 장기 기억
│   └── data.zip의 기타 데이터
├── .env.example
├── requirements.txt
└── README.md
```

## PyCharm 실행 방법

1. ZIP을 압축 해제합니다.
2. PyCharm에서 `long_term_memory_console_project` 폴더를 엽니다.
3. Python 3.11 가상환경을 생성합니다.
4. PyCharm Terminal에서 패키지를 설치합니다.

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

5. `.env.example`을 복사해 `.env`를 만들고 사용할 API 키를 입력합니다.
6. `main.py`를 실행합니다.

```bash
python main.py
```

## 저장소 보호 방식

- `data/user_profiles.json`: data.zip에서 제공된 원본으로 읽기 전용 취급
- `data/user_profiles_rw.json`: JSON 쓰기 실습용 복사본
- `data/profiles.db`: SQLite 실습용 데이터베이스
- 메뉴 9를 실행하면 JSON 복사본과 SQLite DB를 원본 상태로 되돌릴 수 있습니다.
