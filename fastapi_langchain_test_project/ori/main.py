# path: app/main.py

# FastAPI 프레임워크의 핵심 클래스 임포트함 (Python 기반의 고성능 웹 API 프레임워크임)
from fastapi import FastAPI  # 이 클래스가 웹에플리케이션 구동을 위한 객체 생성용임
from app.routers.summarize_router import router as summarize_router 
# 이 라우터 안에는 /api/, /api/summarize 같은 앤드포인트들이 들어 있음

app = FastAPI(title="PDF Summarizer (LangChain + FastAPI)") # 웹 서버 전체 대표하는 객체 생성
# title 인자: 자동 생성되는 API 문서 (Swagger UI, ReDoc)에 표시될 서비스 제목 (브라우저 상단에 노출됨)
# app 객체가 라우팅 관리, 미들웨어 관리, 요청(Request) -> 앤드포인트연결 실행 --> 응답(Response) 전체 흐름을 담당함

app.include_router(summarize_router)  # 라우터 등록
# 외부 파일로 정의된 APIRouter 를 현재 FastAPI 에플리케이션에 장착하는 역할의 코드임
