# -*- coding: utf-8 -*-
"""PyCharm에서 우클릭으로 FastAPI 서버를 실행하기 위한 진입 파일입니다."""

# ASGI 서버 실행을 위해 uvicorn을 가져옵니다.
import uvicorn

# 이 파일을 직접 실행한 경우에만 개발 서버를 시작합니다.
if __name__ == "__main__":
    # 자동 재시작 없이 안정적인 단일 프로세스 개발 서버를 실행합니다.
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
