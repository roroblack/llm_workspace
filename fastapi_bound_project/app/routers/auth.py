"""회원가입과 로그인을 처리하는 라우터입니다."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import TokenResponse, UserCreate, UserResponse
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["회원 인증"])


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="회원가입",
)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """새로운 회원을 등록합니다."""
    # 이미 존재하는 아이디인지 확인합니다.
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        # 중복 리소스는 409 Conflict가 의미상 정확합니다.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 사용 중인 아이디입니다.",
        )

    new_user = User(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        name=user_data.name,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=TokenResponse, summary="로그인")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """아이디와 비밀번호로 로그인하고 JWT 액세스 토큰을 발급합니다.

    Swagger의 Authorize(자물쇠) 기능과 연동되도록
    OAuth2PasswordRequestForm(폼 형식)을 사용합니다.
    """
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username})
    return TokenResponse(access_token=access_token, token_type="bearer")
