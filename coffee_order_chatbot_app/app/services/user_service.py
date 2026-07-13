# app/services/user_service.py
# 회원(회원정보) 관련 비즈니스 로직을 담당하는 서비스 계층입니다.

from sqlalchemy.orm import Session  # DB 세션 타입 힌트에 사용합니다.
from app.models import User  # users 테이블 ORM 모델입니다.
from app.schemas import UserCreate  # 회원가입 요청 스키마입니다.
from app.security import hash_password, verify_password  # 비밀번호 해싱/검증 유틸입니다.


def get_user_by_username(db: Session, username: str) -> User | None:
    # 아이디로 회원을 조회합니다. 없으면 None을 반환합니다.
    return db.query(User).filter(User.username == username).first()  # 첫 번째 일치 회원을 반환합니다.


def create_user(db: Session, user_data: UserCreate) -> User:
    # 신규 회원을 생성해 DB에 저장합니다. 아이디 중복이면 ValueError를 발생시킵니다.
    if get_user_by_username(db, user_data.username):  # 동일 아이디가 이미 있는지 확인합니다.
        raise ValueError("이미 사용 중인 아이디입니다.")  # 중복이면 서비스 계층 오류를 발생시킵니다.

    new_user = User(  # DB에 저장할 새 User ORM 객체를 만듭니다.
        username=user_data.username,  # 요청에서 받은 아이디입니다.
        password_hash=hash_password(user_data.password),  # 원문 비밀번호를 해시하여 저장합니다.
        name=user_data.name,  # 요청에서 받은 이름입니다.
    )
    db.add(new_user)  # 세션에 추가합니다.
    db.commit()  # INSERT를 DB에 반영합니다.
    db.refresh(new_user)  # 자동 생성된 id/created_at을 객체에 반영합니다.
    return new_user  # 생성된 회원을 반환합니다.


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    # 아이디/비밀번호를 검증합니다. 실패하면 None을 반환합니다.
    user = get_user_by_username(db, username)  # 아이디로 회원을 조회합니다.
    if not user:  # 회원이 없으면 인증 실패입니다.
        return None  # None을 반환합니다.
    if not verify_password(password, user.password_hash):  # 비밀번호를 검증합니다.
        return None  # 불일치면 인증 실패입니다.
    return user  # 인증 성공 시 회원을 반환합니다.
