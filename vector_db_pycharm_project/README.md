# Vector DB PyCharm 실습 프로젝트

이 프로젝트는  **대량 검색과 인덱스 저장, 벡터DB 역할, FAISS vs Chroma, 인덱스 영속화, FAISS 인덱스 생성, 저장/재로드, 메타데이터 필터링, 증분 업데이트, 정리 체크리스트**를 PyCharm에서 실행할 수 있도록 정리한 Python 프로젝트입니다.

## 1. 프로젝트 핵심 개념

벡터DB 실습의 핵심은 다음입니다.

```text
비싼 임베딩은 한 번 수행한다.
만든 인덱스는 디스크에 저장한다.
서비스에서는 저장된 인덱스를 로드해 검색만 수행한다.
문서가 추가되면 새 문서만 증분 추가한다.
특정 문서 안에서만 검색해야 하면 metadata filter를 사용한다.
```

## 2. 프로젝트 구조

```text
vector_db_pycharm_project_commented/
├─ src/
│  ├─ common.py                         # 공통 경로, 로컬 임베딩, 문서 로드, 청킹, 출력 함수
│  ├─ 01_numpy_limit_demo.py             # 대량 검색과 NumPy 전체 비교 한계 설명
│  ├─ 02_vector_db_role.py               # 인덱싱과 서비스 분리 설명
│  ├─ 03_faiss_vs_chroma.py              # FAISS와 Chroma 비교 설명
│  ├─ 04_build_index.py                  # FAISS 인덱스 생성 및 저장
│  ├─ 05_service_search.py               # 저장된 FAISS 인덱스 로드 후 검색
│  ├─ 06_save_reload_score.py            # save_local/load_local 및 점수 검색
│  ├─ 07_chroma_filter_search.py         # Chroma metadata filter 검색
│  ├─ 08_incremental_update.py           # FAISS add_documents 증분 업데이트
│  ├─ 09_checklist_summary.py            # 15강 핵심 정리 체크리스트
│  └─ main.py                            # 메뉴 방식 통합 실행 파일
├─ data/
│  ├─ docs/                              # 샘플 TXT 문서
│  └─ indexes/                           # 실행 시 생성되는 FAISS/Chroma 인덱스
├─ requirements.txt                      # 설치 패키지 목록
├─ .gitignore                            # Git 제외 파일 설정
├─ .env.example                          # 환경 변수 예시 파일
└─ README.md                             # 실행 설명서
```

## 3. PyCharm 실행 방법

### 3-1. 프로젝트 열기

1. PyCharm 실행
2. `File` → `Open`
3. 압축 해제한 프로젝트 폴더 선택
4. `Trust Project` 선택

### 3-2. 가상환경 만들기

PyCharm Terminal에서 실행합니다.

```bash
python -m venv .venv
```

Windows PowerShell:

```bash
.venv\Scriptsctivate
```

Windows CMD:

```bash
.venv\Scriptsctivate.bat
```

macOS/Linux:

```bash
source .venv/bin/activate
```

### 3-3. 패키지 설치

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

## 4. 환경 변수 설정

기본 실습은 API 키가 필요 없습니다. 로컬 해시 임베딩을 사용합니다.

실제 Google Gemini 임베딩을 사용하려면 `.env.example`을 복사해 `.env`로 만들고 값을 수정합니다.

```bash
copy .env.example .env
```

`.env` 예시:

```env
EMBEDDING_BACKEND=google
GOOGLE_API_KEY=본인_API_KEY
GOOGLE_EMBEDDING_MODEL=models/text-embedding-004

# EMBEDDING_BACKEND=openai
# OPENAI_API_KEY=여기에_본인_API_KEY_입력
# OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

API 키 없이 실습하려면 다음 상태를 유지합니다.

```env
EMBEDDING_BACKEND=local
```

## 5. 실행 순서

### 방법 1. 메뉴 방식 실행

PyCharm에서 `src/main.py`를 실행합니다.

또는 터미널에서 실행합니다.

```bash
cd src
python main.py
```

메뉴에서 1~9번을 선택해 각 실습을 실행합니다.

### 방법 2. 파일별 실행

인덱스 생성:

```bash
cd src
python 04_build_index.py
```

저장된 인덱스 검색:

```bash
python 05_service_search.py
```

저장/재로드/점수 검색:

```bash
python 06_save_reload_score.py
```

Chroma 메타데이터 필터 검색:

```bash
python 07_chroma_filter_search.py
```

FAISS 증분 업데이트:

```bash
python 08_incremental_update.py
```

## 6. 학습 포인트

### FAISS 인덱싱

`FAISS.from_documents(chunks, emb)`는 모든 청크를 임베딩하고 인덱스를 생성합니다. 비용이 드는 작업이므로 배치 단계에서 한 번만 실행합니다.

### FAISS 영속화

`save_local()`은 인덱스를 `index.faiss`와 `index.pkl`로 저장합니다. `load_local()`은 저장된 벡터를 다시 읽기 때문에 재임베딩하지 않습니다.

### Chroma 메타데이터 필터

`filter={"source": "멤버십정책.txt"}`를 사용하면 특정 문서 안에서만 검색할 수 있습니다.

### 증분 업데이트

`add_documents(new_chunks)`는 새 청크만 임베딩하여 기존 인덱스에 추가합니다. 기존 문서를 다시 임베딩하지 않기 때문에 비용과 시간이 절약됩니다.

## 7. 주의 사항

`allow_dangerous_deserialization=True`는 FAISS의 `index.pkl`을 로드하기 위해 필요합니다. 이 옵션은 직접 생성한 신뢰할 수 있는 인덱스 파일에만 사용해야 합니다. 외부에서 받은 알 수 없는 pickle 파일은 절대 로드하지 마세요.

## 8. 권장 실습 순서

1. `01_numpy_limit_demo.py`
2. `02_vector_db_role.py`
3. `03_faiss_vs_chroma.py`
4. `04_build_index.py`
5. `05_service_search.py`
6. `06_save_reload_score.py`
7. `07_chroma_filter_search.py`
8. `08_incremental_update.py`
9. `09_checklist_summary.py`

## 9. GitHub 업로드 예시

```bash
git init
git add .
git commit -m "Add vector DB FAISS Chroma PyCharm practice project"
git branch -M main
git remote add origin 본인_깃허브_저장소_URL
git push -u origin main
```
