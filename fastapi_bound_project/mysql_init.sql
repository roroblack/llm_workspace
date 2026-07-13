-- MySQL root 계정에서 실습용 데이터베이스를 생성하는 SQL입니다.
CREATE DATABASE IF NOT EXISTS fastapi_db
DEFAULT CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

-- 생성 확인
SHOW DATABASES;

-- 데이터베이스 사용 지정
USE fastapi_db;
SELECT DATABASE();

-- 4. 사용자 생성
CREATE USER 'fastapi'@'localhost'
IDENTIFIED BY 'fastapi80';

-- 5. 사용자 확인
SELECT user, host
FROM mysql.user;

-- 6. 권한 부여
GRANT ALL PRIVILEGES
ON fastapi_db.*
TO 'fastapi'@'localhost';

-- 7. 권한 적용
FLUSH PRIVILEGES;

-- 8. 권한 확인
SHOW GRANTS FOR 'fastapi_user'@'localhost';

/*
MySQL WorkBench 의 메뉴로 실행하는 방법 :
Workbench 접속
→ Create Schema
→ Server > Users and Privileges
→ Add Account
→ Schema Privileges
→ Add Entry
→ 권한 체크
→ Apply
*/

-- 생성한 데이터베이스를 사용합니다.
USE fastapi_db;

-- 테이블은 FastAPI 앱 실행 시 SQLAlchemy가 자동 생성합니다.
