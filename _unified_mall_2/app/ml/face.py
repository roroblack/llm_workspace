"""얼굴 임베딩 + 패시브 라이브니스 (Phase 13, 로컬 CPU).

임베딩: insightface FaceAnalysis(buffalo_l, onnxruntime/CPU) — 정규화 512차원.
라이브니스: Silent-Face MiniFASNetV2 ONNX(패시브, 단일 프레임) — [live, print, replay] softmax.
둘 다 lazy 로드·싱글턴 캐시. 모델 로드 실패는 ConfigError, 입력 문제(얼굴 없음/복수/이미지
파손)는 ValidationErr — 조용히 통과시키지 않는다(무폴백).

한계(정직 기록): (1) Silent-Face 단일 모델(원본 2모델 앙상블 아님). (2) 이 헤드리스 환경에서는
실 웹캠 라이브 vs 사진 쌍으로 정확도를 검증할 수 없어 임계값은 라이브러리 근사 기본값이다.
(3) 재생영상·딥페이크·카메라 주입 공격 및 공인 PAD(iBeta 등) 성능을 보장하지 않는다.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import numpy as np

from app.core.config import get_settings
from app.core.errors import ConfigError, ValidationErr


@lru_cache(maxsize=1)
def _get_face_app():
    try:
        from insightface.app import FaceAnalysis
    except Exception as exc:  # noqa: BLE001
        raise ConfigError(f"insightface import 실패: {exc}") from exc

    settings = get_settings()
    try:
        app = FaceAnalysis(name=settings.FACE_EMBED_MODEL, providers=["CPUExecutionProvider"])
        app.prepare(ctx_id=-1, det_size=(640, 640))
    except Exception as exc:  # noqa: BLE001 - 모델 준비 실패는 명시적 실패
        raise ConfigError(f"얼굴 임베딩 모델 로드 실패({settings.FACE_EMBED_MODEL}): {exc}") from exc
    return app


@lru_cache(maxsize=1)
def _get_antispoof_session():
    import onnxruntime as ort

    settings = get_settings()
    path = settings.FACE_ANTISPOOF_ONNX
    if not path.exists():
        raise ConfigError(
            f"라이브니스 ONNX 모델이 없습니다: {path}. "
            "`python -m scripts.fetch_face_model`로 내려받으세요."
        )
    try:
        return ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    except Exception as exc:  # noqa: BLE001
        raise ConfigError(f"라이브니스 모델 로드 실패: {exc}") from exc


def _decode_image(image_bytes: bytes) -> np.ndarray:
    if not image_bytes:
        raise ValidationErr("이미지 데이터가 비어 있습니다.")
    import cv2

    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)  # BGR
    if img is None:
        raise ValidationErr("이미지를 디코드할 수 없습니다(형식 확인).")
    return img


def _detect_single_face(bgr: np.ndarray):
    """정확히 한 명의 얼굴만 허용(0명/복수는 사용성 오류 — 신원/라이브니스 정보 누출 아님)."""
    app = _get_face_app()
    faces = app.get(bgr)
    if not faces:
        raise ValidationErr("얼굴이 감지되지 않았습니다. 얼굴을 화면 중앙에 맞춰 다시 촬영하세요.")
    if len(faces) > 1:
        raise ValidationErr("얼굴이 여러 개 감지되었습니다. 한 사람만 나오게 촬영하세요.")
    return faces[0]


def _get_new_box(src_w: int, src_h: int, bbox_xywh: tuple[float, float, float, float], scale: float):
    """Silent-Face 원본 크롭 로직 — bbox 중심 기준 scale배 확대 후 이미지 경계로 클램프."""
    x, y, bw, bh = bbox_xywh
    scale = min((src_h - 1) / bh, (src_w - 1) / bw, scale)
    nw, nh = bw * scale, bh * scale
    cx, cy = x + bw / 2, y + bh / 2
    lx, ly = cx - nw / 2, cy - nh / 2
    rx, ry = cx + nw / 2, cy + nh / 2
    if lx < 0:
        rx -= lx
        lx = 0
    if ly < 0:
        ry -= ly
        ly = 0
    if rx > src_w - 1:
        lx -= rx - (src_w - 1)
        rx = src_w - 1
    if ry > src_h - 1:
        ly -= ry - (src_h - 1)
        ry = src_h - 1
    return int(lx), int(ly), int(rx), int(ry)


def _liveness_prob(bgr: np.ndarray, bbox: np.ndarray) -> float:
    """live 클래스 확률(0~1). 값이 클수록 실제 촬영일 가능성이 높다."""
    import cv2

    settings = get_settings()
    h, w = bgr.shape[:2]
    x1, y1, x2, y2 = [float(v) for v in bbox]
    lx, ly, rx, ry = _get_new_box(w, h, (x1, y1, x2 - x1, y2 - y1), settings.FACE_ANTISPOOF_SCALE)
    crop = bgr[ly:ry, lx:rx]
    if crop.size == 0:
        raise ValidationErr("얼굴 영역을 잘라낼 수 없습니다. 다시 촬영하세요.")
    crop = cv2.resize(crop, (80, 80))  # BGR 80x80
    blob = crop.astype(np.float32).transpose(2, 0, 1)[None]  # NCHW

    sess = _get_antispoof_session()
    out = sess.run(None, {sess.get_inputs()[0].name: blob})[0][0]
    e = np.exp(out - out.max())
    prob = e / e.sum()
    return float(prob[0])  # [live, print, replay]


def analyze_face(image_bytes: bytes) -> dict[str, Any]:
    """디코드 → 단일 얼굴 → 라이브니스 → 임베딩. 게이트 순서를 이 함수가 강제한다.

    라이브니스는 임베딩 전에 계산하되, 통과 여부 판정(임계 비교)은 호출자가 하도록
    확률·bool을 함께 돌려준다(호출자가 무폴백 게이트를 구성).
    """
    settings = get_settings()
    bgr = _decode_image(image_bytes)
    face = _detect_single_face(bgr)
    live_prob = _liveness_prob(bgr, face.bbox)
    is_live = live_prob >= settings.FACE_LIVENESS_THRESHOLD
    return {
        "embedding": np.asarray(face.normed_embedding, dtype=np.float32),
        "live_prob": round(live_prob, 4),
        "is_live": is_live,
    }


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0.0:
        return 0.0
    return float(np.dot(a, b) / denom)


def embedding_to_bytes(embedding: np.ndarray) -> bytes:
    return np.asarray(embedding, dtype=np.float32).tobytes()


def embedding_from_bytes(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)
