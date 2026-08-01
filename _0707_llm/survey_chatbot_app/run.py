# uvicorn 서버를 실행하기 위한 진입 파일입니다.
import socket

import uvicorn


def find_available_port(host: str, start_port: int, max_attempts: int = 100) -> int:
    # 시작 포트부터 순서대로 바인딩 가능한 포트를 찾습니다.
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((host, port))
            except OSError:
                continue

            return port

    raise RuntimeError(f"{start_port}번부터 {max_attempts}개 포트 중 사용 가능한 포트가 없습니다.")


# 이 파일을 직접 실행했을 때만 서버를 시작합니다.
if __name__ == "__main__":
    host = "127.0.0.1"
    preferred_port = 8000
    port = find_available_port(host, preferred_port)

    if port != preferred_port:
        print(f"{preferred_port}번 포트가 사용 중입니다. 대신 {port}번 포트로 실행합니다.")

    # app.main 모듈의 app 객체를 FastAPI 서버로 실행합니다.
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
