# app/routers/menus.py
# 메뉴(메뉴정보) CRUD API를 정의하는 라우터 파일입니다.

from fastapi import APIRouter, Depends, HTTPException, status  # 라우터, 의존성 주입, HTTP 오류를 사용합니다.
from sqlalchemy.orm import Session  # DB 세션 타입 힌트에 사용합니다.
from app.database import get_db  # DB 세션 의존성 함수입니다.
from app.models import User  # 로그인 사용자 타입 힌트에 사용합니다.
from app.schemas import MenuCreate, MenuResponse, MenuUpdate  # 메뉴 요청/응답 스키마입니다.
from app.security import get_current_user  # 로그인 사용자 확인 의존성 함수입니다.
from app.services import menu_service  # 메뉴 비즈니스 로직 서비스 계층입니다.

router = APIRouter(prefix="/menus", tags=["메뉴"] )  # /menus로 시작하는 메뉴 API 그룹을 만듭니다.


@router.post("", response_model=MenuResponse, status_code=status.HTTP_201_CREATED)
def create_menu(menu_data: MenuCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 로그인한 사용자가 메뉴를 등록하는 API입니다.
    try:  # 메뉴 이름 중복 시 서비스가 ValueError를 던집니다.
        return menu_service.create_menu(db, menu_data)  # 메뉴를 생성해 반환합니다.
    except ValueError as exc:  # 이름 중복 등 규칙 위반입니다.
        raise HTTPException(status_code=400, detail=str(exc))  # 400 오류로 변환합니다.


@router.get("", response_model=list[MenuResponse])
def get_menus(only_available: bool = False, db: Session = Depends(get_db)):
    # 메뉴 전체 목록을 조회하는 API입니다. only_available=true면 판매 가능 메뉴만 반환합니다.
    return menu_service.list_menus(db, only_available=only_available)  # 메뉴 목록을 반환합니다.


@router.get("/{menu_id}", response_model=MenuResponse)
def get_menu(menu_id: int, db: Session = Depends(get_db)):
    # 메뉴 상세를 조회하는 API입니다.
    menu = menu_service.get_menu(db, menu_id)  # 메뉴를 조회합니다.
    if not menu:  # 없으면 404 오류를 반환합니다.
        raise HTTPException(status_code=404, detail="메뉴를 찾을 수 없습니다.")  # 미존재 오류입니다.
    return menu  # 메뉴 상세를 반환합니다.


@router.put("/{menu_id}", response_model=MenuResponse)
def update_menu(menu_id: int, menu_data: MenuUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 로그인한 사용자가 메뉴를 수정하는 API입니다.
    menu = menu_service.update_menu(db, menu_id, menu_data)  # 메뉴를 부분 수정합니다.
    if not menu:  # 대상이 없으면 404 오류를 반환합니다.
        raise HTTPException(status_code=404, detail="메뉴를 찾을 수 없습니다.")  # 미존재 오류입니다.
    return menu  # 수정된 메뉴를 반환합니다.


@router.delete("/{menu_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu(menu_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 로그인한 사용자가 메뉴를 삭제하는 API입니다.
    deleted = menu_service.delete_menu(db, menu_id)  # 메뉴를 삭제합니다.
    if not deleted:  # 대상이 없으면 404 오류를 반환합니다.
        raise HTTPException(status_code=404, detail="메뉴를 찾을 수 없습니다.")  # 미존재 오류입니다.
    return None  # 204 응답은 본문이 없습니다.
