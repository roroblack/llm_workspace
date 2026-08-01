"""
로컬 PyCharm에서 FastAPI 개발 서버를 실행하는 진입 파일입니다.
"""

# 운영체제 환경변수를 읽기 위해 os 모듈을 가져옵니다.
import os

# FastAPI 애플리케이션을 실행할 ASGI 서버인 uvicorn을 가져옵니다.
import uvicorn


def main() -> None:
    """
    .env 또는 운영체제 환경변수의 HOST와 PORT를 읽어 서버를 실행합니다.
    """

    # HOST 환경변수가 없으면 로컬 전용 주소인 127.0.0.1을 사용합니다.
    host = os.getenv("HOST", "127.0.0.1")

    # PORT 환경변수가 없으면 FastAPI 예제에서 자주 사용하는 8000번을 사용합니다.
    port = int(os.getenv("PORT", "8000"))

    # 문자열로 전달된 RELOAD 값을 소문자로 바꾸고 true인지 확인합니다.
    reload_enabled = os.getenv("RELOAD", "true").lower() == "true"

    # app.main 모듈의 app 객체를 Uvicorn 서버로 실행합니다.
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload_enabled,
    )


# 이 파일을 직접 실행한 경우에만 main 함수를 호출합니다.
if __name__ == "__main__":
    main()
