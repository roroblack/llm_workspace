"""얼굴 2차 인증 테스트 (실 insightface + Silent-Face ONNX, @ml — CI 제외).

실행: pytest -m ml tests/test_face.py

주의: 라이브니스 모델은 정지 사진 크롭을 위조(spoof)로 판정하는 게 정상 동작이다(사진/화면
= 위조). 따라서 신원 매칭·토큰 흐름을 종단 검증하는 테스트는 라이브니스 임계값을 0으로 낮춰
(정지 이미지도 통과) 로직만 확인한다 — 실 웹캠 라이브 얼굴 수용은 이 환경에서 검증 불가.
"""

from __future__ import annotations

import io
import uuid

import cv2
import numpy as np
import pytest

from app.core.config import get_settings
from app.ml.face import analyze_face, cosine_similarity

pytestmark = pytest.mark.ml


def _single_face_jpgs():
    """insightface 샘플 t1에서 단일 얼굴 크롭 3장(동일인 2장 + 타인 1장) JPEG 바이트."""
    import insightface
    from insightface.app import FaceAnalysis

    app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=-1, det_size=(640, 640))
    img = insightface.data.get_image("t1")
    faces = sorted(app.get(img), key=lambda f: float(f.bbox[0]))

    def crop(face, margin):
        x1, y1, x2, y2 = face.bbox
        w, h = x2 - x1, y2 - y1
        X1, Y1 = max(0, int(x1 - w * margin)), max(0, int(y1 - h * margin))
        X2 = min(img.shape[1], int(x2 + w * margin))
        Y2 = min(img.shape[0], int(y2 + h * margin))
        ok, buf = cv2.imencode(".jpg", img[Y1:Y2, X1:X2])
        return buf.tobytes()

    return crop(faces[0], 0.6), crop(faces[0], 0.85), crop(faces[1], 0.6)


_A1, _A2, _B1 = _single_face_jpgs()


def test_embedding_same_person_high_similarity():
    ra1 = analyze_face(_A1)
    ra2 = analyze_face(_A2)
    assert cosine_similarity(ra1["embedding"], ra2["embedding"]) >= 0.40


def test_embedding_different_person_low_similarity():
    ra1 = analyze_face(_A1)
    rb1 = analyze_face(_B1)
    assert cosine_similarity(ra1["embedding"], rb1["embedding"]) < 0.40


def test_liveness_returns_valid_probability():
    r = analyze_face(_A1)
    assert 0.0 <= r["live_prob"] <= 1.0
    assert isinstance(r["is_live"], bool)


@pytest.fixture
def relax_liveness():
    """정지 사진도 라이브니스를 통과하도록 임계값을 0으로 (신원/토큰 로직만 검증)."""
    s = get_settings()
    old = s.FACE_LIVENESS_THRESHOLD
    s.FACE_LIVENESS_THRESHOLD = 0.0
    yield
    s.FACE_LIVENESS_THRESHOLD = old


def _signup_login(client):
    u = f"face_{uuid.uuid4().hex[:8]}"
    client.post("/auth/signup", json={"username": u, "password": "pass1234"})
    r = client.post("/auth/login", data={"username": u, "password": "pass1234"})
    body = r.json()
    return u, body["access_token"]  # 얼굴 미등록이라 바로 토큰


def _img_file(b: bytes):
    return {"image": ("face.jpg", io.BytesIO(b), "image/jpeg")}


def test_no_face_user_logs_in_without_2fa(client):
    u, token = _signup_login(client)
    assert token  # 얼굴 미등록 → access_token 즉시 발급
    r = client.post("/auth/login", data={"username": u, "password": "pass1234"})
    assert r.json()["face_2fa_required"] is False


def test_face_register_requires_auth(client):
    r = client.post("/api/face/register", files=_img_file(_A1))
    assert r.status_code == 401


def test_full_2fa_flow_match_and_mismatch(client, relax_liveness):
    u, token = _signup_login(client)
    hdr = {"Authorization": f"Bearer {token}"}

    # 등록(로그인 세션 전용)
    r = client.post("/api/face/register", files=_img_file(_A1), headers=hdr)
    assert r.status_code == 200 and r.json()["registered"] is True

    # 이제 로그인하면 얼굴 2차인증 요구(access_token 없음, challenge만)
    r = client.post("/auth/login", data={"username": u, "password": "pass1234"})
    body = r.json()
    assert body["face_2fa_required"] is True
    assert body.get("access_token") is None
    challenge = body["challenge_token"]
    ch_hdr = {"Authorization": f"Bearer {challenge}"}

    # 같은 사람 얼굴 → 최종 토큰 발급
    r = client.post("/auth/login/face", files=_img_file(_A2), headers=ch_hdr)
    assert r.status_code == 200
    final = r.json()["access_token"]
    assert final

    # 타인 얼굴 → 실패(일반 메시지, 토큰 없음)
    r2 = client.post("/auth/login", data={"username": u, "password": "pass1234"})
    ch2 = {"Authorization": f"Bearer {r2.json()['challenge_token']}"}
    r = client.post("/auth/login/face", files=_img_file(_B1), headers=ch2)
    assert r.status_code == 401


def test_pre2fa_token_rejected_by_protected_endpoint(client, relax_liveness):
    u, token = _signup_login(client)
    hdr = {"Authorization": f"Bearer {token}"}
    client.post("/api/face/register", files=_img_file(_A1), headers=hdr)

    r = client.post("/auth/login", data={"username": u, "password": "pass1234"})
    challenge = r.json()["challenge_token"]
    # pre2fa 토큰으로 보호 리소스 접근 시도 → 거부
    r = client.get("/api/face/status", headers={"Authorization": f"Bearer {challenge}"})
    assert r.status_code == 401
