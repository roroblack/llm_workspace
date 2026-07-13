# uvicorn 서버를 파이썬 파일로 실행하기 위해 uvicorn을 불러옵니다.
import uvicorn

# 이 파일을 직접 실행했을 때만 아래 코드가 실행되도록 합니다.
if __name__ == "__main__":
    # FastAPI 앱을 개발 모드로 실행합니다.
    uvicorn.run("app.main:app", host="127.0.0.1", port=8001, reload=True)
