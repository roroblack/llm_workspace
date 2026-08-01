# app/security.py
# 비밀번호 해싱, 비밀번호 검증, JWT 토큰 생성/해석 기능을 모아둔 보안 유틸 파일입니다.

import os  # .env에서 보안 설정값을 읽기 위해 사용합니다.
from datetime import datetime, timedelta, timezone  # JWT 만료 시간을 계산하기 위해 사용합니다.
from dotenv import load_dotenv  # .env 파일을 환경변수로 불러옵니다.
from fastapi import Depends, HTTPException, status  # 인증 실패 응답과 의존성 주입에 사용합니다.
from fastapi.security import OAuth2PasswordBearer  # Swagger Authorize 버튼과 Bearer 토큰 인증에 사용합니다.
from jose import JWTError, jwt  # JWT 토큰 인코딩과 디코딩에 사용합니다.
from passlib.context import CryptContext  # 안전한 비밀번호 해싱을 위해 사용합니다.
from sqlalchemy.orm import Session  # DB 세션 타입 힌트에 사용합니다.
from app.database import get_db  # DB 세션 의존성 함수입니다.
from app.models import User  # 현재 로그인 사용자를 조회하기 위해 User 모델을 가져옵니다.

load_dotenv()  # .env 파일 값을 환경변수로 등록합니다.

SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key")  # JWT 서명에 사용할 비밀키입니다.
ALGORITHM = os.getenv("ALGORITHM", "HS256")  # JWT 서명 알고리즘입니다.
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))  # 토큰 만료 시간입니다.

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")  # bcrypt 방식으로 비밀번호를 해싱합니다.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")  # Swagger에서 로그인 API를 토큰 발급 URL로 인식하게 합니다.


def hash_password(password: str) -> str:
    # 사용자가 입력한 원문 비밀번호를 DB 저장용 해시 문자열로 변환합니다.
    return pwd_context.hash(password)  # bcrypt 해시 결과를 반환합니다.


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # 로그인 시 입력한 원문 비밀번호와 DB에 저장된 해시 비밀번호가 일치하는지 검증합니다.
    return pwd_context.verify(plain_password, hashed_password)  # 일치하면 True, 아니면 False를 반환합니다.


def create_access_token(data: dict) -> str:
    # JWT 액세스 토큰을 생성합니다.
    to_encode = data.copy()  # 원본 데이터가 변경되지 않도록 복사합니다.
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)  # 만료 시각을 계산합니다.
    to_encode.update({"exp": expire})  # JWT payload에 만료 시각을 추가합니다.
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  # payload를 서명하여 JWT 문자열로 변환합니다.
    return encoded_jwt  # 완성된 JWT 토큰을 반환합니다.


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    # 보호된 API에서 현재 로그인 사용자를 확인하는 의존성 함수입니다.
    credentials_exception = HTTPException(  # 토큰 검증 실패 시 반환할 401 오류 객체입니다.
        status_code=status.HTTP_401_UNAUTHORIZED,  # 인증 실패 HTTP 상태 코드입니다.
        detail="인증 정보가 올바르지 않습니다.",  # 클라이언트에 전달할 오류 메시지입니다.
        headers={"WWW-Authenticate": "Bearer"},  # Bearer 인증 실패임을 나타냅니다.
    )
    try:  # JWT 디코딩 과정에서 오류가 날 수 있으므로 try 문을 사용합니다.
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  # 토큰을 검증하고 payload를 추출합니다.
        username: str | None = payload.get("sub")  # payload에서 사용자 아이디를 꺼냅니다.
        if username is None:  # 사용자 아이디가 없으면 잘못된 토큰입니다.
            raise credentials_exception  # 401 오류를 발생시킵니다.
    except JWTError:  # 토큰 위조, 만료, 형식 오류가 발생한 경우입니다.
        raise credentials_exception  # 401 오류를 발생시킵니다.

    user = db.query(User).filter(User.username == username).first()  # 토큰의 username으로 DB에서 회원을 조회합니다.
    if user is None:  # DB에 해당 사용자가 없으면 인증 실패입니다.
        raise credentials_exception  # 401 오류를 발생시킵니다.
    return user  # 인증된 현재 사용자 객체를 반환합니다.
