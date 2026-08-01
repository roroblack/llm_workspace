# 제28강 Project Design PyCharm 콘솔 프로젝트


## 실행 환경

- Python 3.11 권장
- PyCharm에서 프로젝트 폴더 열기
- 가상환경 생성 후 `pip install -r requirements.txt`
- `.env.example`을 `.env`로 복사하고 API 키 입력
- `main.py` 실행

## 메뉴

1. 환경·데이터 확인
2. 통합 CS 에이전트 설계 스켈레톤
3. RAG·메모리·멀티에이전트 트레이드오프 판단
4. 실습문제 1 설계 문서 생성
5. 실습문제 2 코드 스켈레톤
6. OpenAI 또는 Gemini를 선택한 설계 검토

HTML 설명 요약 메뉴는 포함하지 않았습니다.

## 테스트

```bash
pytest -q
```

LLM 호출 메뉴를 제외한 테스트는 API 키 없이 실행됩니다.
