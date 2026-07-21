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


# 토큰 stage(Phase 13 얼굴 2차인증):
#   "full"   — 정상 접근 토큰(모든 보호 리소스 접근 가능)
#   "pre2fa" — 비밀번호는 통과했으나 얼굴 2차인증 대기 중인 단명 토큰(얼굴 단계에서만 유효)
STAGE_FULL = "full"
STAGE_PRE2FA = "pre2fa"


def create_access_token(
    subject: str,
    settings: Settings | None = None,
    stage: str = STAGE_FULL,
    expires_minutes: int | None = None,
) -> str:
    settings = settings or get_settings()
    secret = settings.require_secret_key()
    minutes = expires_minutes if expires_minutes is not None else settings.ACCESS_TOKEN_EXPIRE_MINUTES
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    payload = {"sub": subject, "exp": expire, "stage": stage}
    return jwt.encode(payload, secret, algorithm=settings.JWT_ALGORITHM)


def _decode(token: str, settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    secret = settings.require_secret_key()
    try:
        return jwt.decode(token, secret, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        raise AuthErr("토큰이 유효하지 않거나 만료되었습니다.") from exc


def decode_token(token: str, settings: Settings | None = None) -> str:
    """토큰에서 username(sub)을 추출. 무효/만료면 AuthErr."""
    payload = _decode(token, settings)
    username = payload.get("sub")
    if not username:
        raise AuthErr("토큰에 사용자 정보가 없습니다.")
    return username


def _user_from_token(token: str, db: Session, *, require_stage: str | None) -> User:
    payload = _decode(token)
    username = payload.get("sub")
    if not username:
        raise AuthErr("토큰에 사용자 정보가 없습니다.")
    # stage 미포함 토큰(구 버전/테스트)은 full로 간주(하위호환).
    stage = payload.get("stage", STAGE_FULL)
    if require_stage is not None and stage != require_stage:
        raise AuthErr("이 토큰으로는 요청한 작업을 수행할 수 없습니다.")
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise AuthErr("사용자를 찾을 수 없습니다.")
    return user


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """정상 접근 토큰만 허용 — pre2fa 단명 토큰은 거부(얼굴 단계 전용)."""
    payload = _decode(token)
    if payload.get("stage", STAGE_FULL) == STAGE_PRE2FA:
        raise AuthErr("얼굴 2차 인증이 완료되지 않았습니다.")
    username = payload.get("sub")
    if not username:
        raise AuthErr("토큰에 사용자 정보가 없습니다.")
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise AuthErr("사용자를 찾을 수 없습니다.")
    return user


def get_pre2fa_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """얼굴 2차인증 단계 전용 — pre2fa stage 토큰만 허용."""
    return _user_from_token(token, db, require_stage=STAGE_PRE2FA)
