@echo off
REM FastAPI ChatGPT 챗봇 앱 실행 스크립트입니다.
REM 먼저 가상환경을 활성화한 뒤 이 파일을 실행하세요.
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
