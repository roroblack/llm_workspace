# RAG 문서 로드·청킹·검색 콘솔 프로젝트

## 주요 기능

1. PDF 페이지 단위 로드와 `Document.page_content`, `metadata` 확인
2. `RecursiveCharacterTextSplitter` 청킹
3. 문자열 키워드 검색의 한계 확인
4. `chunk_size`, `chunk_overlap` 조합 비교
5. CSV, TXT, Markdown 문서 로더 비교
6. PyTorch 해시 벡터와 코사인 유사도 기반 로컬 검색
7. 검색 근거를 사용한 OpenAI/Gemini 답변 생성

## PyCharm 실행 순서

1. PyCharm에서 이 프로젝트 폴더를 엽니다.
2. Python 3.11 가상환경을 생성합니다.
3. PyCharm Terminal에서 다음 명령을 실행합니다.

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

4. API 메뉴도 실행하려면 `.env.example`을 복사해 `.env`로 만들고 API 키를 입력합니다.
5. `code/main.py`를 마우스 오른쪽 버튼으로 클릭하고 **Run 'main'**을 선택합니다.

API 키가 없어도 1~7번 메뉴는 실행할 수 있습니다.

## 프로젝트 구조

```text
rag_console_pycharm_project/
├─ code/
│  ├─ common.py
│  ├─ main.py
│  └─ features/
│     ├─ document_service.py
│     ├─ local_vector_service.py
│     ├─ llm_service.py
│     └─ menu_actions.py
├─ data/
│  ├─ docs/환불교환정책.pdf
│  ├─ faq.csv
│  ├─ notice.txt
│  └─ policy.md
├─ .env.example
├─ .gitignore
├─ requirements.txt
└─ README.md
```

## 참고

PyTorch 로컬 검색은 API 없이 실행 구조를 이해하기 위한 해시 기반 단어 벡터 예제입니다. 실제 의미 기반 검색 품질이 필요한 경우 `common.py`의 `get_embeddings()`와 FAISS·Chroma·Qdrant 같은 벡터 DB를 연결해야 합니다.
