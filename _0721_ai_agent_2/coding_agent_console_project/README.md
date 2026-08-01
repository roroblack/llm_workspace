# 제23강 Coding Agent PyCharm 콘솔 프로젝트

## 프로젝트 목적

`common.py`의 `get_chat()`과 `DATA` 경로를 공통으로 사용하고, `data.zip`에서 제공된 `buggy_script.py`와 `sales_daily.csv`를 이용해 코딩 에이전트의 핵심 루프를 실행합니다.

- 코드 읽기
- LLM을 이용한 버그 수정
- LLM 응답에서 코드블록만 추출
- 원본을 보존하고 새 파일로 저장
- `subprocess` 격리 실행
- 종료코드 기반 검증
- 실제 오류를 다시 LLM에 전달하는 self-debugging
- OpenAI / Gemini 선택
- 실습문제 해답 실행

HTML 파일과 references 폴더는 포함하지 않으며, HTML 내용을 정리해 출력하는 메뉴도 없습니다.

## PyCharm 실행 순서

1. ZIP 압축을 풉니다.
2. PyCharm에서 `coding_agent_console_project` 폴더를 엽니다.
3. Python 3.10 이상 인터프리터를 선택합니다.
4. PyCharm Terminal에서 다음 명령을 실행합니다.

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

5. `.env.example`을 복사해 `.env`를 만들고 API 키를 입력합니다.
6. `main.py`를 실행합니다.

## 메뉴

```text
1. data.zip 데이터 파일 및 sales_daily.csv 확인
2. 원본 buggy_script.py 실행 오류 확인
3. 코드 읽기·LLM 수정 요청·코드블록 추출
4. 수정본 새 파일 저장·격리 실행·종료코드 검증
5. 재귀적 버그 수정 오류 피드백 루프
6. 코드블록 추출 정규식 단독 확인
8-1. 실습문제 해답 1 — 변경 요약과 코드 분리
8-2. 실습문제 해답 2 — 새 버그 파일 self-debugging
9. OpenAI / Gemini 다시 선택
0. 종료
```

## 안전 원칙

- 원본 `data/buggy_script.py`는 덮어쓰지 않습니다.
- 수정 결과는 `fixed_script.py` 등 새 파일에 저장합니다.
- 생성 코드는 현재 앱과 분리된 하위 프로세스에서 실행합니다.
- 타임아웃으로 무한루프를 차단합니다.
- self-debugging은 최대 3회로 제한합니다.
- AI 수정 결과는 최종 배포 전에 사람이 검토해야 합니다.
