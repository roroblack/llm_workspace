# app/routers/auth.py
# 회원가입과 로그인 API를 정의하는 라우터 파일입니다.

from fastapi import APIRouter, Depends, HTTPException, status  # 라우터, 의존성 주입, 오류 응답을 사용합니다.
from fastapi.security import OAuth2PasswordRequestForm  # Swagger 로그인 폼 데이터를 받기 위해 사용합니다.
from sqlalchemy.orm import Session  # DB 세션 타입 힌트에 사용합니다.
from app.database import get_db  # DB 세션을 주입받기 위해 사용합니다.
from app.models import User  # users 테이블 ORM 모델입니다.
from app.schemas import TokenResponse, UserCreate, UserResponse  # 요청/응답 스키마입니다.
from app.security import create_access_token, hash_password, verify_password  # 보안 유틸 함수입니다.

router = APIRouter(prefix="/auth", tags=["회원 인증"] )  # /auth로 시작하는 인증 관련 API 그룹을 만듭니다.


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    # 간단 회원가입 API입니다.
    existing_user = db.query(User).filter(User.username == user_data.username).first()  # 동일 아이디가 있는지 조회합니다.
    if existing_user:  # 이미 존재하는 아이디라면 가입을 막습니다.
        raise HTTPException(status_code=400, detail="이미 사용 중인 아이디입니다.")  # 400 오류를 반환합니다.

    new_user = User(  # DB에 저장할 새 User ORM 객체를 생성합니다.
        username=user_data.username,  # 요청에서 받은 아이디를 저장합니다.
        password_hash=hash_password(user_data.password),  # 원문 비밀번호를 해시하여 저장합니다.
        name=user_data.name,  # 요청에서 받은 이름을 저장합니다.
    )
    db.add(new_user)  # 새 회원 객체를 DB 세션에 추가합니다.
    db.commit()  # INSERT 쿼리를 실제 DB에 반영합니다.
    db.refresh(new_user)  # DB에서 자동 생성된 id와 created_at 값을 객체에 반영합니다.
    return new_user  # 가입된 회원 정보를 반환합니다.


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 간단 로그인 API입니다.
    # Swagger Authorize와 호환되도록 JSON이 아니라 x-www-form-urlencoded 형식의 username/password를 받습니다.
    user = db.query(User).filter(User.username == form_data.username).first()  # 아이디로 회원을 조회합니다.
    if not user:  # 회원이 없으면 로그인 실패입니다.
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다.")  # 401 오류를 반환합니다.

    if not verify_password(form_data.password, user.password_hash):  # 입력 비밀번호와 저장된 해시를 비교합니다.
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다.")  # 401 오류를 반환합니다.

    access_token = create_access_token(data={"sub": user.username})  # username을 subject로 넣어 JWT를 생성합니다.
    return TokenResponse(access_token=access_token, token_type="bearer")  # 클라이언트에 토큰을 반환합니다.
