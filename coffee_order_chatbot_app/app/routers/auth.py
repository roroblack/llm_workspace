# app/routers/auth.py
# 회원가입과 로그인 API를 정의하는 라우터 파일입니다.

from fastapi import APIRouter, Depends, HTTPException, status  # 라우터, 의존성 주입, 오류 응답을 사용합니다.
from fastapi.security import OAuth2PasswordRequestForm  # Swagger 로그인 폼 데이터를 받기 위해 사용합니다.
from sqlalchemy.orm import Session  # DB 세션 타입 힌트에 사용합니다.
from app.database import get_db  # DB 세션을 주입받기 위해 사용합니다.
from app.schemas import TokenResponse, UserCreate, UserResponse  # 요청/응답 스키마입니다.
from app.security import create_access_token  # JWT 토큰 생성 유틸입니다.
from app.services import user_service  # 회원 관련 비즈니스 로직을 담은 서비스 계층입니다.

router = APIRouter(prefix="/auth", tags=["회원 인증"])  # /auth로 시작하는 인증 관련 API 그룹을 만듭니다.


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    # 간단 회원가입 API입니다. 실제 저장 로직은 user_service가 담당합니다.
    try:  # 서비스 계층에서 중복 아이디 시 ValueError를 던집니다.
        new_user = user_service.create_user(db, user_data)  # 회원을 생성합니다.
    except ValueError as exc:  # 아이디 중복 등 비즈니스 규칙 위반입니다.
        raise HTTPException(status_code=400, detail=str(exc))  # 400 오류로 변환해 반환합니다.
    return new_user  # 가입된 회원 정보를 반환합니다.


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 간단 로그인 API입니다.
    # Swagger Authorize와 호환되도록 JSON이 아니라 x-www-form-urlencoded 형식의 username/password를 받습니다.
    user = user_service.authenticate_user(db, form_data.username, form_data.password)  # 아이디/비밀번호를 검증합니다.
    if not user:  # 인증 실패 시 401 오류를 반환합니다.
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다.")  # 401 오류입니다.

    access_token = create_access_token(data={"sub": user.username})  # username을 subject로 넣어 JWT를 생성합니다.
    return TokenResponse(access_token=access_token, token_type="bearer")  # 클라이언트에 토큰을 반환합니다.
