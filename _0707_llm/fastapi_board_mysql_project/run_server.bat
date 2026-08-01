@echo off
REM Windows CMD에서 FastAPI 개발 서버를 실행하는 배치 파일입니다.
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
