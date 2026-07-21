"""얼굴 임베딩 + 패시브 라이브니스 + 품질 게이팅 (Phase 13, 로컬 CPU).

파이프라인(무폴백): 디코드 → 단일 얼굴 → **품질 게이팅**(흐림·밝기·크기·자세·검출신뢰도) →
라이브니스 → 정렬(112×112) → 저조도 조건부 CLAHE → 임베딩. 저품질은 조용히 통과시키지 않고
명시적 재촬영 사유를 돌려준다(ValidationErr). 모델 로드 실패는 ConfigError.

인식률 관련(실측 근거): 검출·모델보다 **정보 손실(블러·저해상)과 등록 오염**이 병목이라,
품질 게이팅 + 다중 이미지 등록(임베딩 평균)이 실질 레버다. CLAHE는 정상광에선 임베딩을 오히려
흔들어(실측) 저조도에서만 조건부 적용한다. insightface(ArcFace)는 CPU 오픈소스의 강한 기준선이며
저품질 특화 AdaFace 스왑은 현재 수치엔 과설계(고정 테스트셋에서 이득 실증 시에만 채택).

한계: 라이브니스는 Silent-Face 단일 모델(앙상블 아님)이고 이 환경에서 실 라이브/사진 쌍으로
정확도 검증 불가. insightface 사전학습 모델은 비상업 연구용 라이선스.
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


def _aligned_crop(bgr: np.ndarray, face) -> np.ndarray:
    from insightface.utils import face_align

    return face_align.norm_crop(bgr, face.kps, image_size=112)  # BGR 112×112


def _check_quality(bgr: np.ndarray, face, aligned: np.ndarray, *, strict: bool) -> None:
    """품질 미달이면 조용히 통과시키지 않고 사유를 담아 ValidationErr(무폴백)."""
    import cv2

    settings = get_settings()
    q = settings.FACE_QUALITY_REGISTER if strict else settings.FACE_QUALITY_VERIFY

    face_px = float(face.bbox[2] - face.bbox[0])
    if face_px < q["min_face_px"]:
        raise ValidationErr("얼굴이 너무 작습니다. 카메라에 조금 더 가까이 와서 다시 촬영하세요.")

    det = float(getattr(face, "det_score", 1.0))
    if det < q["min_det"]:
        raise ValidationErr("얼굴이 뚜렷하지 않습니다. 정면을 보고 다시 촬영하세요.")

    gray = cv2.cvtColor(aligned, cv2.COLOR_BGR2GRAY)
    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    if blur < q["min_blur"]:
        raise ValidationErr("이미지가 흐릿합니다. 흔들림 없이 초점을 맞춰 다시 촬영하세요.")

    bright = float(gray.mean())
    if bright < q["min_bright"]:
        raise ValidationErr("너무 어둡습니다. 조명을 밝게 하고 다시 촬영하세요.")
    if bright > q["max_bright"]:
        raise ValidationErr("너무 밝습니다(과노출). 조명을 낮추고 다시 촬영하세요.")

    # pose = [pitch, yaw, roll] (insightface). roll은 정렬로 보정되므로 pitch·yaw만 본다.
    pose = getattr(face, "pose", None)
    if pose is not None:
        pitch, yaw = abs(float(pose[0])), abs(float(pose[1]))
        if yaw > q["max_yaw"] or pitch > q["max_pitch"]:
            raise ValidationErr("고개가 많이 돌아가 있습니다. 정면을 바라보고 다시 촬영하세요.")


def _maybe_clahe(aligned: np.ndarray) -> np.ndarray:
    """정렬 crop 평균 밝기가 임계 미만(저조도)일 때만 luminance에 약한 CLAHE(등록·검증 동일)."""
    import cv2

    settings = get_settings()
    gray = cv2.cvtColor(aligned, cv2.COLOR_BGR2GRAY)
    if float(gray.mean()) >= settings.FACE_CLAHE_BRIGHTNESS:
        return aligned  # 정상광엔 적용 안 함(정상광 CLAHE는 임베딩을 흔든다 — 실측)
    lab = cv2.cvtColor(aligned, cv2.COLOR_BGR2LAB)
    lch, ach, bch = cv2.split(lab)
    lch = cv2.createCLAHE(clipLimit=settings.FACE_CLAHE_CLIP, tileGridSize=(8, 8)).apply(lch)
    return cv2.cvtColor(cv2.merge((lch, ach, bch)), cv2.COLOR_LAB2BGR)


def _embed(aligned: np.ndarray) -> np.ndarray:
    app = _get_face_app()
    rec = app.models["recognition"]
    feat = rec.get_feat(aligned).flatten().astype(np.float32)
    norm = float(np.linalg.norm(feat))
    if norm == 0.0:
        raise ValidationErr("임베딩을 계산할 수 없습니다. 다시 촬영하세요.")
    return feat / norm


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


def _get_new_box(src_w: int, src_h: int, bbox_xywh, scale: float):
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


def analyze_face(image_bytes: bytes, *, strict: bool = False) -> dict[str, Any]:
    """디코드 → 단일 얼굴 → 품질 게이팅 → 라이브니스 → 정렬 → 조건부 CLAHE → 임베딩.

    게이트 순서를 이 함수가 강제한다. 품질 미달/얼굴 문제는 ValidationErr(명시적 재촬영),
    라이브니스 통과 여부 판정은 호출자가 하도록 확률·bool을 함께 돌려준다.
    """
    settings = get_settings()
    bgr = _decode_image(image_bytes)
    face = _detect_single_face(bgr)
    aligned = _aligned_crop(bgr, face)
    _check_quality(bgr, face, aligned, strict=strict)  # 품질 미달이면 여기서 실패
    live_prob = _liveness_prob(bgr, face.bbox)
    is_live = live_prob >= settings.FACE_LIVENESS_THRESHOLD
    embedding = _embed(_maybe_clahe(aligned))
    return {"embedding": embedding, "live_prob": round(live_prob, 4), "is_live": is_live}


def average_embeddings(embeddings: list[np.ndarray]) -> np.ndarray:
    """다중 등록: 품질 통과 임베딩들을 평균 후 재정규화(견고한 기준 임베딩)."""
    if not embeddings:
        raise ValidationErr("등록에 사용할 유효한 얼굴이 없습니다.")
    mean = np.mean(np.stack(embeddings), axis=0).astype(np.float32)
    norm = float(np.linalg.norm(mean))
    if norm == 0.0:
        raise ValidationErr("등록 임베딩을 계산할 수 없습니다. 다시 촬영하세요.")
    return mean / norm


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
