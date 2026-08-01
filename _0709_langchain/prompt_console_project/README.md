# Prompt Engineering Console Project

## 1. 프로젝트 구성

```text
prompt_console_project/
├─ src/
│  ├─ common.py              # API 키, 모델, DATA 경로 공통 모듈
│  ├─ main.py                # 콘솔 메뉴 실행 파일
│  ├─ llm_clients.py         # Gemini/OpenAI API 호출 함수
│  ├─ html_code_reader.py    # HTML 설명/코드 블록 추출 함수
│  └─ torch_demo.py          # PyTorch 텐서 정확도 계산 실습
├─ data/
│  ├─ cs_inquiries.csv       # 고객 문의 분류 실습 데이터
│  └─ docs/source_html/      # 제공된 HTML 강의 파일
├─ code_snippets/            # HTML 코드 블록 추출 결과 저장 폴더
├─ .env.example              # API 키 설정 예시
├─ requirements.txt          # 설치 패키지 목록
├─ .gitignore
└─ README.md
```

## 2. PyCharm 실행 순서

1. PyCharm에서 `prompt_console_project` 폴더를 엽니다.
2. Python Interpreter를 선택합니다. 권장 버전은 Python 3.11 입니다.
3. PyCharm Terminal에서 아래 명령을 실행합니다.

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

4. `.env.example` 파일을 복사해서 `.env` 파일을 만듭니다.

```bash
copy .env.example .env
```

5. `.env` 파일에 본인의 API 키를 입력합니다.

```env
GOOGLE_API_KEY=본인_Gemini_API_KEY
OPENAI_API_KEY=본인_OpenAI_API_KEY
```

6. `src/main.py`를 실행합니다.

```bash
python src/main.py
```

## 3. 메뉴 설명

- `0`: 프로젝트 경로, 데이터 파일 로드 상태 확인
- `1`: HTML 강의 파일의 제목, 설명, 코드 블록 개수 확인
- `2`: HTML 코드 블록을 `code_snippets` 폴더에 txt/json으로 저장
- `3`: Gemini API로 4요소 기반 정중 답변 생성
- `4`: Gemini API로 few-shot 고객 문의 분류
- `5`: Gemini API로 JSON 출력 강제 실습
- `6`: Gemini API로 프롬프트 인젝션 방어 실습
- `7`: OpenAI API로 답변 생성 및 분류 실습
- `8`: Gemini API로 CSV 전체 분류 후 정확도 측정
- `9`: PyTorch 텐서로 정확도 계산 원리 확인

## 4. API 키 없이 확인 가능한 메뉴

API 키가 없어도 아래 메뉴는 실행됩니다.

- `0`: 프로젝트 정보 확인
- `1`: HTML 설명/코드 블록 확인
- `2`: HTML 코드 블록 추출
- `9`: PyTorch 텐서 정확도 계산 데모

Gemini/OpenAI API 메뉴는 `.env` 파일에 키를 입력해야 실행됩니다.
