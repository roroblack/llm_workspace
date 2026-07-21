"""얼굴 라이브니스 ONNX 모델(Silent-Face MiniFASNetV2) 다운로드.

`data/models/minifasnet_v2.onnx`가 없으면 HuggingFace에서 내려받는다(약 1.7MB, Apache-2.0).
insightface 임베딩 모델(buffalo_l)은 최초 사용 시 자동 다운로드되므로 여기서 받지 않는다.
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

from app.core.config import get_settings

_URL = "https://huggingface.co/garciafido/minifasnet-v2-anti-spoofing-onnx/resolve/main/minifasnet_v2.onnx"


def main() -> None:
    out: Path = get_settings().FACE_ANTISPOOF_ONNX
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and out.stat().st_size > 0:
        print(f"[fetch_face_model] 이미 존재: {out} ({out.stat().st_size} bytes)")
        return
    print(f"[fetch_face_model] 다운로드 중: {_URL}")
    urllib.request.urlretrieve(_URL, out)
    print(f"[fetch_face_model] 완료: {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
