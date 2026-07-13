# RAG QA Console Project

## 주요 기능

1. 공통 모듈과 데이터 경로 확인
2. 정책 PDF 로드 및 청킹
3. LCEL 기반 RAG QA 체인(InMemoryVectorStore)
4. 답변과 출처를 함께 반환하는 `answer()` 함수
5. 문서에 없는 질문의 환각 억제 확인
6. 검색 결과 개수 `k=2`, `k=4`, `k=6` 비교
7. PyTorch 코사인 유사도 재정렬
8. LLM 관련도 점수 재정렬

## 프로젝트 구조

```text
rag_qa_console_project/
├─ code/
│  ├─ common.py
│  ├─ rag_service.py
│  └─ main.py
├─ data/
│  └─ docs/
│     ├─ 환불교환정책.pdf
│     └─ 멤버십정책.pdf
├─ .env.example
├─ .gitignore
├─ requirements.txt
└─ README.md
```

## PyCharm에서 실행

1. ZIP 파일의 압축을 해제합니다.
2. PyCharm에서 `Open`을 선택합니다.
3. `rag_qa_console_pycharm_project` 폴더를 선택합니다.
4. Python 3.11 인터프리터를 생성합니다.
5. PyCharm Terminal에서 다음 명령을 실행합니다.

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

6. `.env.example`을 복사하여 `.env` 파일을 만듭니다.
7. 사용할 API 키를 입력합니다.

```env
OPENAI_API_KEY=실제_OpenAI_API_KEY
GOOGLE_API_KEY=실제_Google_API_KEY
```

8. `code/main.py`를 실행합니다.

터미널에서는 다음 명령으로 실행할 수 있습니다.

```bash
python code/main.py
```

## API 키 없이 실행 가능한 메뉴

- 1번: 공통 모듈과 프로젝트 데이터 확인
- 2번: 정책 PDF 로드 및 청킹 확인

3번부터 8번 메뉴는 선택한 제공자의 API 키가 필요합니다. 7번은 유사도 계산 자체는 PyTorch로 수행하지만 질문과 청크 임베딩 생성에 OpenAI 또는 Gemini 임베딩 API를 사용합니다.

## 구현 핵심

- `common.py`의 `get_chat()`과 `get_embeddings()`를 공통 진입점으로 사용합니다.
- Windows OpenMP DLL 충돌을 막기 위해 `faiss-cpu`를 제거하고 `InMemoryVectorStore`를 사용합니다.
- 검색 결과 안에서만 답하도록 프롬프트를 제한합니다.
- 검색 문서를 먼저 보관한 뒤 답변과 `sources`를 함께 반환합니다.
- `temperature=0`을 사용해 사실 기반 답변의 일관성을 높입니다.
- `k`를 크게 하여 후보를 넓게 찾은 뒤 PyTorch 또는 LLM으로 다시 정렬할 수 있습니다.

## OpenMP 오류 해결 내용

기존 프로젝트는 `torch`와 `faiss-cpu`가 서로 다른 OpenMP 런타임을 동시에 로드해 다음 오류가 발생할 수 있었습니다.

```text
OMP: Error #15: Initializing libomp140.x86_64.dll, but found libiomp5md.dll already initialized.
```

수정본에서는 다음과 같이 해결했습니다.

1. `requirements.txt`에서 `faiss-cpu` 제거
2. `rag_service.py`의 `FAISS` import 제거
3. `InMemoryVectorStore`로 벡터 저장소 교체
4. ZIP에서 깨진 PDF 한글 파일명 복원
5. 특정 PDF 이름을 하드코딩하지 않고 `data/docs/*.pdf` 전체 자동 로드

기존 가상환경에는 FAISS DLL이 남아 있을 수 있으므로 반드시 기존 `.venv`를 삭제하고 새로 설치하십시오.

```bat
rmdir /s /q .venv
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
python code\main.py
```
