# 멀티에이전트 Supervisor 콘솔 프로젝트

## 주요 학습 기능

- 추천 전문 에이전트와 정책 전문 에이전트의 역할·도구 분리
- Supervisor 중앙 라우팅
- 규칙 기반 라우터
- LLM 기반 의미 라우터
- 규칙 우선, 애매할 때만 LLM을 호출하는 하이브리드 라우터
- PyTorch 텐서를 이용한 라우터 정확도 계산
- OpenAI와 Gemini 공급자 선택
- CSV 기반 상품·FAQ 검색 도구


## 프로젝트 구조

```text
multi_agent_supervisor_console_project/
├── code/
│   ├── common.py             # 제공된 공통 모듈
│   ├── main.py               # 콘솔 메뉴 진입점
│   ├── agents.py             # 역할별 전문 에이전트
│   ├── supervisor.py         # 중앙 Supervisor
│   ├── router.py             # 규칙/LLM/하이브리드 라우터
│   ├── data_repository.py    # CSV 검색 도구
│   ├── torch_evaluation.py   # PyTorch 정확도 평가
│   └── message_utils.py      # LLM 응답 호환 처리
├── data/
│   ├── products.csv
│   └── faq.csv
├── tests/
│   └── test_rules.py
├── .env.example
├── requirements.txt
└── README.md
```

## PyCharm에서 실행

1. ZIP 파일을 원하는 폴더에 압축 해제합니다.
2. PyCharm에서 `Open`을 선택하고 프로젝트 폴더를 엽니다.
3. Python 3.11 가상환경을 생성합니다.
4. PyCharm Terminal에서 다음 명령을 실행합니다.

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

5. `.env.example`을 복사하여 `.env` 파일을 만듭니다.
6. 사용할 API 키를 입력합니다.
7. `code/main.py`를 마우스 오른쪽 버튼으로 클릭하고 `Run 'main'`을 선택합니다.

터미널에서 실행할 수도 있습니다.

```bash
python code/main.py
```

## API 키 없이 실행 가능한 메뉴

- 1번: 환경 확인
- 3번: 상품 CSV 도구
- 4번: FAQ CSV 도구
- 10번: PyTorch 규칙 라우터 평가

전문 에이전트, LLM 라우터, 하이브리드 비교는 선택한 공급자의 API 키가 필요합니다.

## 테스트

외부 API를 호출하지 않는 단위 테스트입니다.

```bash
pytest -q
```
