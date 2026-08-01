# 임베딩 콘솔 실습 프로젝트

## 주요 기능

- PyTorch 코사인 유사도 계산
- Gemini/OpenAI 문장 임베딩
- 문장 간 의미 유사도 비교
- FAQ 배치 임베딩과 Top-k 검색
- 긴 문서 청킹 후 청크별 임베딩 검색
- 검색 근거를 사용하는 Gemini/OpenAI 답변 생성

HTML 페이지의 설명을 보여 주는 메뉴는 포함하지 않았습니다.

## 실행 환경

- Python 3.11 권장
- PyCharm

## 실행 순서

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

`.env.example`을 복사하여 `.env`를 만든 뒤 필요한 API 키를 입력합니다.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

실행:

```bash
python code/main.py
```

API 키가 없어도 1번과 2번 메뉴는 실행할 수 있습니다. 3~7번 메뉴는 선택한 제공자의 API 키가 필요합니다.
