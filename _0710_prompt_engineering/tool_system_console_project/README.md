# 제6강 Tool System 콘솔 실습 프로젝트

## 1. 프로젝트 구조

```text
tool_system_console_project/
├─ app/
│  ├─ main.py              # 콘솔 메뉴 실행 파일
│  ├─ common.py            # 제공된 공통 모듈
│  ├─ data_tools.py        # 가격/재고/주문/검색 도구 함수
│  ├─ torch_demo.py        # PyTorch 텐서 분석
│  ├─ gemini_tools.py      # Gemini Function Calling 실습
│  └─ openai_tools.py      # OpenAI Tool Calling 실습
├─ data/
│  ├─ products.csv         # 상품 정보
│  ├─ inventory.csv        # 재고 정보
│  └─ orders.csv           # 주문 정보
├─ .env.example            # API 키 예시 파일
├─ requirements.txt        # 설치 패키지
├─ .gitignore
└─ README.md
```

## 2. 실행 방법

```bash
cd tool_system_console_project
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
copy .env.example .env
python app/main.py
```

`.env` 파일에 실제 키를 입력하면 Gemini/OpenAI 메뉴를 실행할 수 있습니다. API 키가 없어도 HTML 확인과 PyTorch 분석 메뉴는 실행됩니다.

## 3. 주요 메뉴

```text
1. PyTorch 상품/재고 텐서 분석
2. Gemini 도구 선택 관찰
3. Gemini 자동 도구 실행
4. Gemini 비슷한 도구 구분 실험
5. OpenAI 도구 선택 관찰
6. OpenAI 도구 실행 후 최종 답변
0. 종료
```

## 4. 학습 핵심

- 도구가 많아지면 올바른 도구 선택이 중요합니다.
- 모델은 함수 본문이 아니라 함수 이름, 인자, 독스트링을 보고 도구를 고릅니다.
- 좋은 도구는 한 가지 일만 하고, 이름과 인자가 명확하며, 독스트링에 “무엇을 하는가”와 “언제 쓰는가”가 들어 있어야 합니다.
- 비슷한 도구는 입력 형태, 결과 건수, 부정 조건을 독스트링에 명확히 적어 구분합니다.
