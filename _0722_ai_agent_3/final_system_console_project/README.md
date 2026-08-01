# Final System PyCharm 콘솔 프로젝트

제공된 `common.py`와 `data.zip`을 사용해 주문·재고·FAQ 도구, 정책 PDF RAG, OpenAI/Gemini, thread_id 단기 메모리, 
멀티턴 시나리오와 실습문제 해답을 하나의 콘솔 앱으로 구성한 프로젝트입니다.

## 프로젝트 특징

- API 키가 없어도 데이터 확인, 주문·재고·FAQ, 오류 검증, 실습문제 1은 실행할 수 있습니다.
- 정책 RAG와 통합 에이전트 메뉴는 선택한 공급자의 API 키가 필요합니다.

## 프로젝트 구조

```text
final_system_console_project/
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── code/
│   ├── common.py
│   ├── app_context.py
│   ├── config_service.py
│   ├── data_tools.py
│   ├── policy_rag.py
│   ├── final_agent.py
│   └── exercises.py
├── data/
│   ├── orders.csv
│   ├── inventory.csv
│   ├── faq.csv
│   ├── config.yaml
│   ├── docs/*.pdf
│   └── data.zip의 나머지 데이터
├── logs/
└── cache/
```

## PyCharm 실행 방법

1. ZIP 파일을 원하는 폴더에 압축 해제합니다.
2. PyCharm에서 **Open**을 눌러 `final_system_console_project` 폴더를 엽니다.
3. Python 3.11 가상환경을 생성합니다.
4. PyCharm Terminal에서 다음 명령을 실행합니다.

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

5. `.env.example`을 복사해 `.env` 파일을 만듭니다.

Windows CMD:

```cmd
copy .env.example .env
```

PowerShell:

```powershell
Copy-Item .env.example .env
```

6. `.env`에 사용할 API 키를 입력합니다.
7. `main.py`를 실행합니다.

```bash
python main.py
```

## 실행 메뉴

```text
1. data.zip 핵심 데이터와 정책 PDF 확인
2. 주문 상태 도구 실행
3. 재고 조회 도구 실행
4. FAQ 검색 도구 실행
5. 정책 RAG 도구 빌드 확인
6. 통합 에이전트 단일 질문
7. 멀티턴 시나리오 데모
8. 에러 케이스 도구 단위 검증
9-1. 실습문제 1 해답: 교환 신청 도구
9-2. 실습문제 2 해답: 메모리 격리
10. OpenAI/Gemini 공급자 다시 선택
0. 종료
```

## 핵심 데이터 도구

- `get_order_status_raw(order_id)`: `orders.csv` 실제 주문 조회
- `get_stock_raw(product_name)`: `inventory.csv` 실제 재고 조회
- `search_faq_raw(keyword)`: `faq.csv` 키워드 검색
- `build_policy_tool(...)`: `data/docs/*.pdf` 전체를 임베딩하고 FAISS retriever 도구로 변환
- `answer(message, thread_id)`: 도구 4개, 정책 RAG, InMemorySaver를 결합한 최종 진입점

## 실습문제 해답

### 실습 1 — 교환 신청 도구

실제 주문번호 존재 여부와 교환 사유를 확인한 뒤 `EX-영숫자6자리` 접수번호를 생성합니다. 실무에서는 이 부분을 데이터베이스 INSERT로 교체합니다.

### 실습 2 — 메모리 격리

서로 다른 `thread_id`를 사용해 A 고객과 B 고객의 대화 기록이 섞이지 않는지 실제 통합 에이전트로 검증합니다.

## 주의사항

- `data/docs`의 PDF 이름이 압축 파일 인코딩 때문에 특수한 문자열로 보일 수 있습니다. 
코드는 파일명을 하드코딩하지 않고 `*.pdf` 전체를 자동 검색하므로 실행에는 문제가 없습니다.
- 정책 RAG를 처음 실행하면 PDF 임베딩 시간이 필요하고 API 사용량이 발생합니다.
- `InMemorySaver`는 프로그램 종료 시 메모리가 사라지는 단기 메모리입니다.
