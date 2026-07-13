# app/database.py
# FastAPI 앱이 데이터베이스(기본 SQLite)와 연결할 때 사용하는 공통 설정 파일입니다.

import os  # 운영체제 환경변수를 읽기 위해 사용하는 표준 라이브러리입니다.
from pathlib import Path  # DB 파일이 저장될 data 폴더 경로를 계산하기 위해 사용합니다.
from dotenv import load_dotenv  # .env 파일에 저장된 환경변수를 파이썬 환경으로 불러옵니다.
from sqlalchemy import create_engine  # SQLAlchemy가 DB 연결 엔진을 만들 때 사용합니다.
from sqlalchemy.orm import declarative_base, sessionmaker  # ORM 모델 기본 클래스와 DB 세션 팩토리를 만듭니다.

load_dotenv()  # 프로젝트 루트의 .env 파일을 읽어 환경변수로 등록합니다.

# data 폴더를 프로젝트 루트 기준으로 계산합니다. (app 폴더의 부모가 프로젝트 루트입니다.)
BASE_DIR = Path(__file__).resolve().parent.parent  # 프로젝트 루트 경로입니다.
DATA_DIR = BASE_DIR / "data"  # SQLite DB 파일을 저장할 data 폴더 경로입니다.
DATA_DIR.mkdir(exist_ok=True)  # data 폴더가 없으면 자동으로 생성합니다.

# DATABASE_URL은 .env 파일에서 읽어옵니다. 없으면 data/coffee.db SQLite 파일을 기본값으로 사용합니다.
# 예: SQLite  -> sqlite:///./data/coffee.db
# 예: MySQL   -> mysql+pymysql://root:1234@localhost:3306/coffee_db?charset=utf8mb4
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'coffee.db'}")  # DB 접속 문자열입니다.

# SQLite는 기본적으로 하나의 스레드에서만 연결을 사용하도록 제한하므로,
# FastAPI의 다중 요청 환경에서는 check_same_thread=False 옵션이 필요합니다.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# create_engine은 SQLAlchemy의 DB 연결 엔진을 생성합니다.
# pool_pre_ping=True는 오래된 연결이 끊어진 경우 자동으로 확인하여 재연결 안정성을 높입니다.
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)  # DB 접속 엔진을 생성합니다.

# sessionmaker는 요청마다 사용할 DB 세션 객체를 만들어주는 공장 역할을 합니다.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # 수동 commit 방식의 세션 팩토리를 만듭니다.

# Base는 SQLAlchemy ORM 모델 클래스들이 상속받는 기준 클래스입니다.
Base = declarative_base()  # ORM 테이블 모델의 부모 클래스를 생성합니다.


def get_db():
    # FastAPI 의존성 주입용 함수입니다.
    # 라우터 함수에서 Depends(get_db)로 사용하면 요청마다 DB 세션을 하나씩 받을 수 있습니다.
    db = SessionLocal()  # 새로운 DB 세션을 생성합니다.
    try:  # 요청 처리 중 예외가 발생해도 세션을 닫기 위해 try-finally를 사용합니다.
        yield db  # 라우터 함수에 DB 세션을 전달합니다.
    finally:  # 요청 처리가 끝난 뒤 항상 실행됩니다.
        db.close()  # DB 세션을 닫아 연결 자원을 반환합니다.
