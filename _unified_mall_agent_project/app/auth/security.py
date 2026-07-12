"""인증: bcrypt 해싱 + JWT 발급/검증 + get_current_user.

SECRET_KEY는 config에서만 가져오며 미설정 시 ConfigError (하드코딩·폴백 금지).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import AuthErr
from app.db.database import get_db
from app.db.models import User

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(raw: str) -> str:
    return _pwd.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    return _pwd.verify(raw, hashed)


def create_access_token(subject: str, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    secret = settings.require_secret_key()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, secret, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str, settings: Settings | None = None) -> str:
    """토큰에서 username(sub)을 추출. 무효/만료면 AuthErr."""
    settings = settings or get_settings()
    secret = settings.require_secret_key()
    try:
        payload = jwt.decode(token, secret, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        raise AuthErr("토큰이 유효하지 않거나 만료되었습니다.") from exc
    username = payload.get("sub")
    if not username:
        raise AuthErr("토큰에 사용자 정보가 없습니다.")
    return username


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    username = decode_token(token)
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise AuthErr("사용자를 찾을 수 없습니다.")
    return user
