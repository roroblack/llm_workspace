# 기본 Python 프로젝트 : LLM Parameter 실습 프로젝트

# 패키지 설치
```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

# 프로젝트 구조
```text
llm_parameter_test_project
    |- .env             # 환경 변수 파일 (env.example 복사 후 실제 키 입력)
    |- env.example      # 환경 변수 예시 파일
    |- requirements.txt # 의존 패키지 목록
    |- src/
    |-      |- main.py              # 실행 진입점 (파라미터 입력 → LLM 호출 → 결과 출력)
    |-      |- llm_app/
    |-      |-      |- __init__.py      # 패키지 초기화 파일
                    |- config.py        # .env load, API Key 확인, 모델명 관리
                    |- llm_service.py   # gemini / openAI 호출 함수
                    |- utils.py         # 콘솔 입력 / 출력 보조 함수
```

# 실행 방법
```bash
# .env 준비 (예시 파일을 복사한 뒤 실제 API Key를 입력)
cp env.example .env

# 실습 프로그램 실행
python src/main.py
```
temperature / top_p / 최대 토큰 수를 바꿔가며 Gemini 또는 OpenAI 응답을 비교해볼 수 있습니다.