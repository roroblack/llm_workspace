# -*- coding: utf-8 -*-
"""PyCharm에서 우클릭 실행할 수 있는 개발 서버 시작 파일입니다."""

# uvicorn은 FastAPI ASGI 애플리케이션을 실행합니다.
import uvicorn

# 직접 실행된 경우에만 개발 서버를 시작합니다.
if __name__ == "__main__":
    # reload=True는 코드 수정 시 서버를 자동 재시작합니다.
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
