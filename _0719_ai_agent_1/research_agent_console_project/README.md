# Research Agent PyCharm 콘솔 프로젝트

## 1. 주요 기능

1. 검색 없는 LLM의 최신 정보 한계 확인
2. DuckDuckGo 검색 도구 기반 리서치 에이전트
3. 검색·네트워크 실패 시 LLM 폴백
4. 마크다운 시장 리포트 자동 저장
5. 복잡한 주제의 하위 검색 질의 분해
6. 여러 하위 질의 검색 결과 종합
7. 서로 다른 검색어 두 개를 이용한 교차 검증
8. `competitor_data.csv` 기반 경쟁사 분석
9. `monthly_sales.csv`와 `products.csv` 기반 내부 데이터 분석
10. 실습문제 1·2 해답 실행

## 2. 프로젝트 구조

```text
research_agent_console_project/
├── main.py
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── code/
│   ├── common.py
│   ├── app_context.py
│   ├── message_utils.py
│   ├── research_service.py
│   ├── deep_research.py
│   ├── cross_check_service.py
│   ├── data_report_service.py
│   └── exercises.py
├── data/
│   └── data.zip에서 추출한 CSV, JSON, PDF 파일
└── reports/
    └── 실행 중 생성되는 Markdown 보고서
```

## 3. PyCharm 실행 방법

### 3-1. 프로젝트 열기

PyCharm에서 `File → Open`을 선택하고 압축을 해제한 `research_agent_console_project` 폴더를 엽니다.

### 3-2. 가상환경 생성

PyCharm 터미널에서 다음 명령을 실행합니다.

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Windows 명령 프롬프트:

```cmd
.venv\Scripts\activate.bat
```

### 3-3. 패키지 설치

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 3-4. API 키 설정

`.env.example`을 복사해 `.env`를 만듭니다.

Windows 명령 프롬프트:

```cmd
copy .env.example .env
```

PowerShell:

```powershell
Copy-Item .env.example .env
```

`.env` 파일에 사용할 공급자의 API 키를 입력합니다.

```dotenv
OPENAI_API_KEY=실제_OpenAI_API_KEY
GOOGLE_API_KEY=실제_Google_API_KEY
```

OpenAI만 사용할 때는 `OPENAI_API_KEY`만 있어도 되고, Gemini만 사용할 때는 `GOOGLE_API_KEY`만 있어도 됩니다.

### 3-5. 앱 실행

PyCharm에서 `main.py`를 마우스 오른쪽 버튼으로 클릭한 뒤 `Run 'main'`을 선택합니다.

터미널에서는 다음과 같이 실행할 수 있습니다.

```bash
python main.py
```

## 4. 실행 메뉴

```text
1. 검색 없는 LLM의 최신 시장 동향 응답 확인
2. 웹 검색 리서치 에이전트 + 자동 폴백 + 리포트 저장
3. 검색 실패 상황을 강제하여 폴백 코드 확인
4. 복잡한 주제 하위 질의 분해 + 심층 조사 + 저장
5. 검색 결과 교차 검증 및 신뢰도 판정
6. data.zip 경쟁사 CSV 기반 리포트 생성
7. data.zip 월별 매출·상품 데이터 기반 내부 리포트
8-1. 실습문제 해답 1 — 경쟁사 CSV 리포트
8-2. 실습문제 해답 2 — 다중 하위 질의 통합
9. OpenAI / Gemini 다시 선택
0. 프로그램 종료
```

## 5. 네트워크와 폴백

웹 검색은 인터넷 연결, 방화벽, 검색 서비스 상태, rate limit에 따라 실패할 수 있습니다. 
검색 코드에는 `try/except`가 적용되어 있습니다.

검색이 실패하면 앱은 종료되지 않고 다음 방식으로 동작합니다.

```text
웹 검색 기반 최신 리포트 실패
→ 선택한 OpenAI 또는 Gemini의 내부 지식으로 임시 리포트 생성
→ 최신 정보가 아닐 수 있다는 경고 문구 표시
→ reports 폴더에 결과 저장
```

메뉴 3은 실제 네트워크 장애가 없어도 폴백 분기를 강제로 실행하여 코드를 확인하는 교육용 메뉴입니다.

## 6. 생성 파일

실행 결과는 `reports/` 폴더에 UTF-8 Markdown 파일로 저장됩니다.

```text
reports/research_YYYY-MM-DD_HHMMSS_주제.md
reports/deep_research_YYYY-MM-DD_HHMMSS_주제.md
reports/competitor_report.md
reports/exercise_multiquery_YYYY-MM-DD_HHMMSS_주제.md
```

## 7. 데이터 사용

다음 파일을 실제 실행 코드에서 사용합니다.

- `data/competitor_data.csv`: 경쟁사 데이터 기반 리포트와 실습문제 1
- `data/monthly_sales.csv`: 내부 판매 동향 분석
- `data/products.csv`: 상품 기준 정보와 판매 분석 결합
- 그 밖의 `data.zip` 파일도 프로젝트의 `data/` 폴더에 그대로 포함

## 8. 주의사항

- 웹 검색 결과는 항상 정확한 공식 자료라고 단정할 수 없습니다.
- 교차 검증 메뉴의 신뢰도는 LLM 보조 판정이므로 중요한 의사결정 전에는 원문과 공식 출처를 사람이 확인해야 합니다.
- 검색 폴백 리포트는 최신 시장 보고서가 아니라 서비스 중단을 막기 위한 임시 결과입니다.

