"""얼굴 등록/상태 라우터 (Phase 13) — 모두 로그인 세션 전용(get_current_user).

등록은 이미 인증된 세션에서만 가능해 체인 잠김을 방지한다(미인증 상태에서 얼굴만으로
등록/로그인하는 경로 없음).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.core.errors import ValidationErr
from app.db.database import get_db
from app.db.models import FaceCredential, User
from app.services import face_service

router = APIRouter(prefix="/api/face", tags=["face"])


class FaceStatusResponse(BaseModel):
    registered: bool


class FaceRegisterResponse(BaseModel):
    registered: bool
    shots_used: int
    shots_submitted: int


@router.get("/status", response_model=FaceStatusResponse)
def face_status(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> FaceStatusResponse:
    return FaceStatusResponse(registered=face_service.has_face(db, user.id))


@router.post("/register", response_model=FaceRegisterResponse)
async def face_register(
    images: list[UploadFile] = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FaceRegisterResponse:
    """다중 이미지 등록(여러 샷을 품질 게이팅 후 임베딩 평균). 단일 샷도 허용."""
    blobs = []
    for f in images:
        b = await f.read()
        if b:
            blobs.append(b)
    if not blobs:
        raise ValidationErr("업로드된 이미지가 비어 있습니다.")
    result = face_service.register_face(db, user, blobs)
    return FaceRegisterResponse(**result)


@router.delete("/register", response_model=FaceStatusResponse)
def face_unregister(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> FaceStatusResponse:
    cred = db.query(FaceCredential).filter(FaceCredential.user_id == user.id).first()
    if cred is not None:
        db.delete(cred)
        db.commit()
    return FaceStatusResponse(registered=False)
