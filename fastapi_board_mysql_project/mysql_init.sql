-- MySQL에서 실습용 데이터베이스를 생성하는 SQL입니다.
CREATE DATABASE IF NOT EXISTS fastapi_board_db
DEFAULT CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

-- 생성한 데이터베이스를 사용합니다.
USE fastapi_board_db;

-- 테이블은 FastAPI 앱 실행 시 SQLAlchemy가 자동 생성합니다.
