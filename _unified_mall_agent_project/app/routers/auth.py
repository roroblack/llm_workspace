"""인증 라우터: 회원가입 / 로그인(JWT 발급)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.security import create_access_token
from app.core.config import get_settings
from app.db.database import get_db
from app.schemas.commerce import SignupRequest, TokenResponse
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse)
def signup(body: SignupRequest, db: Session = Depends(get_db)) -> TokenResponse:
    # SECRET_KEY preflight: 토큰 발급 불가 상태면 유저를 만들기 전에 실패시킨다
    # (Codex 지적: 이전엔 유저 commit 후 토큰 발급 단계에서 실패해 유저가 잔존)
    get_settings().require_secret_key()
    user = user_service.signup(db, body.username, body.password)
    return TokenResponse(access_token=create_access_token(user.username))


@router.post("/login", response_model=TokenResponse)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = user_service.authenticate(db, form.username, form.password)
    return TokenResponse(access_token=create_access_token(user.username))
