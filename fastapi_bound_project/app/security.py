"""비밀번호 해싱과 JWT 인증을 담당하는 모듈입니다."""

import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User

load_dotenv()

# JWT 설정을 환경 변수에서 읽어옵니다.
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# bcrypt를 사용하는 비밀번호 해시 컨텍스트입니다.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Swagger의 Authorize(자물쇠)와 연동되는 OAuth2 password 흐름입니다.
# tokenUrl은 로그인 엔드포인트 경로와 일치해야 합니다.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def hash_password(password: str) -> str:
    """평문 비밀번호를 해시로 변환합니다."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """평문 비밀번호가 해시와 일치하는지 확인합니다."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """전달받은 데이터로 JWT 액세스 토큰을 생성합니다."""
    to_encode = data.copy()
    # timezone-aware(UTC)로 만료 시각을 계산합니다.
    # datetime.utcnow()는 Python 3.12+에서 deprecated이므로 사용하지 않습니다.
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """토큰을 검증하고 현재 로그인한 사용자를 반환하는 의존성 함수입니다."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보를 확인할 수 없습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    return user
