# KoGPT2 한국어 챗봇 Streamlit 프로젝트

이 프로젝트는 제공된 `GPT_KoGPT2_torch_한글깨짐수정.ipynb` 노트북의 KoGPT2 문장 생성 코드를 PyCharm에서 실행 가능한 앱 구조로 정리한 Streamlit 챗봇 프로젝트입니다.

핵심 모델은 Hugging Face의 `skt/kogpt2-base-v2`를 사용하며, 노트북에서 한글 출력 깨짐 문제를 줄이기 위해 적용한 다음 방식을 그대로 반영했습니다.

```python
from transformers import PreTrainedTokenizerFast, GPT2LMHeadModel

tokenizer = PreTrainedTokenizerFast.from_pretrained(
    model_name,
    bos_token='</s>',
    eos_token='</s>',
    unk_token='<unk>',
    pad_token='<pad>',
    mask_token='<mask>'
)

model = GPT2LMHeadModel.from_pretrained(model_name)
```

## 1. 프로젝트 구조

```text
kogpt2_streamlit_chatbot_project/
├─ app/
│  └─ streamlit_app.py
├─ src/
│  ├─ __init__.py
│  ├─ chatbot.py
│  ├─ config.py
│  └─ utils/
│     ├─ __init__.py
│     └─ text_cleaner.py
├─ .gitignore
├─ README.md
└─ requirements.txt
```

## 2. 주요 기능

- KoGPT2 기반 한국어 문장 생성
- Streamlit 채팅 화면 구현
- 대화 이력 기반 짧은 문맥 유지
- 생성 옵션 조절
  - 최대 생성 토큰 수
  - temperature
  - top-p
  - top-k
  - repetition penalty
  - no-repeat n-gram
- 마지막 입력 문장의 토큰 ID와 토큰 문자열 확인
- 특수 토큰과 깨진 문자 후처리
- PyCharm 프로젝트 구조 적용

## 3. 실행 환경

권장 환경은 다음과 같습니다.

- Python 3.10 또는 3.11
- PyCharm
- Windows 10/11 또는 macOS/Linux
- 인터넷 연결 필요  
  최초 실행 시 Hugging Face Hub에서 KoGPT2 모델과 토크나이저를 다운로드합니다.

## 4. 설치 방법

### 4.1 PyCharm에서 프로젝트 열기

1. PyCharm 실행
2. `File > Open`
3. 압축 해제한 `kogpt2_streamlit_chatbot_project` 폴더 선택
4. Python Interpreter를 새 가상환경으로 설정

### 4.2 터미널에서 가상환경 생성

Windows CMD 기준입니다.

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

PowerShell 기준입니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

macOS/Linux 기준입니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

## 5. 앱 실행 방법

프로젝트 루트 폴더에서 다음 명령을 실행합니다.

```bash
streamlit run app/streamlit_app.py
```

실행 후 브라우저가 자동으로 열리지 않으면 터미널에 표시되는 주소를 브라우저에 붙여 넣습니다.

보통 다음 주소입니다.

```text
http://localhost:8501
```

## 6. 사용 방법

1. 채팅 입력창에 한국어 질문 또는 시작 문장을 입력합니다.
2. 왼쪽 사이드바에서 생성 옵션을 조절할 수 있습니다.
3. 답변이 너무 짧으면 `최대 생성 토큰 수`를 늘립니다.
4. 답변이 너무 반복되면 `반복 패널티`를 높입니다.
5. 답변이 너무 단조로우면 `Temperature`를 조금 높입니다.
6. 답변이 너무 엉뚱하면 `Temperature`와 `Top-p`를 낮춥니다.

## 7. 코드 설명

### `app/streamlit_app.py`

Streamlit 화면을 담당합니다.

- 페이지 제목 설정
- 사이드바 생성 옵션 구성
- 채팅 메시지 출력
- 사용자 입력 처리
- 모델 답변 표시
- 토큰 분석 결과 출력

### `src/chatbot.py`

KoGPT2 모델 로딩과 답변 생성을 담당합니다.

- `PreTrainedTokenizerFast`로 KoGPT2 토크나이저 로딩
- `GPT2LMHeadModel`로 KoGPT2 모델 로딩
- GPU 또는 CPU 자동 선택
- `generate()`를 사용한 문장 생성
- 대화 이력 기반 답변 생성

### `src/utils/text_cleaner.py`

문자열 후처리를 담당합니다.

- 깨진 문자 제거
- 특수 토큰 제거
- 반복 공백 제거
- 대화 프롬프트 생성
- 생성 결과에서 답변 부분만 추출

### `src/config.py`

공통 설정값을 담당합니다.

- 모델 이름
- 기본 생성 옵션
- 첫 화면 환영 메시지

## 8. Git 사용 명령

### 8.1 Git 저장소 초기화

```bash
git init
```

### 8.2 현재 파일 상태 확인

```bash
git status
```

### 8.3 전체 파일 스테이징

```bash
git add .
```

### 8.4 첫 커밋 생성

```bash
git commit -m "Initial KoGPT2 Streamlit chatbot project"
```

### 8.5 GitHub 원격 저장소 연결

GitHub에서 새 Repository를 만든 뒤, 저장소 주소를 복사하여 아래 명령에 넣습니다.

```bash
git remote add origin https://github.com/사용자명/저장소명.git
```

### 8.6 기본 브랜치를 main으로 변경

```bash
git branch -M main
```

### 8.7 GitHub로 푸시

```bash
git push -u origin main
```

### 8.8 이후 수정 작업 반영

```bash
git status
git add .
git commit -m "Update chatbot app"
git push
```

### 8.9 팀 프로젝트 브랜치 생성 예시

```bash
git checkout -b member1
git add .
git commit -m "Add member1 feature"
git push -u origin member1
```

## 9. 주의사항

KoGPT2 기본 모델은 범용 한국어 생성 모델이며, ChatGPT처럼 지시문을 완벽히 따르는 대화 전용 모델은 아닙니다. 따라서 질문에 대한 정확한 정답형 답변보다는 입력 문맥을 이어 쓰는 방식에 가깝습니다.

더 자연스러운 챗봇을 만들려면 다음 개선이 필요합니다.

- 대화 데이터셋으로 추가 파인튜닝
- instruction tuning 모델 사용
- 검색 기반 RAG 구조 추가
- 금칙어 필터링 및 답변 안전성 검사 추가
- 대화 이력 요약 기능 추가

## 10. 패키지 오류 해결 팁

PyTorch 설치에서 오류가 발생하면 먼저 pip를 업그레이드합니다.

```bash
python -m pip install --upgrade pip setuptools wheel
```

CUDA 버전 문제가 있으면 CPU 버전으로 먼저 실행하는 것이 가장 단순합니다.

```bash
pip install torch
```

Streamlit 실행 중 `ModuleNotFoundError: No module named 'src'`가 발생하면 반드시 프로젝트 루트 폴더에서 실행해야 합니다.

```bash
streamlit run app/streamlit_app.py
```
