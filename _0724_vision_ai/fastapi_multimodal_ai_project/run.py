"""PyCharm에서 실행 버튼만 눌러 FastAPI 개발 서버를 시작하는 파일입니다."""

# ASGI 서버인 uvicorn을 가져옵니다.
import uvicorn


# 이 파일을 직접 실행했을 때만 서버를 시작합니다.
if __name__ == "__main__":
    # reload=True는 코드 변경 시 개발 서버를 자동 재시작합니다.
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
