"""브라우저 녹음 파일을 저장하고 Whisper STT로 텍스트 변환합니다."""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from importlib import metadata
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings

logger = logging.getLogger(__name__)

_active_backend: str | None = None
_last_stt_error: str | None = None


def select_stt_device() -> str:
    """STT 작업자가 사용할 장치를 결정합니다."""
    configured = settings.whisper_device.strip().lower()
    if configured in {"cpu", "cuda"}:
        return configured
    # Windows에서는 CUDA용 CTranslate2 DLL 의존성을 피하기 위해 CPU를 기본값으로 사용합니다.
    if os.name == "nt":
        return "cpu"
    # 다른 운영체제에서도 안정성을 우선하여 기본값은 CPU입니다.
    return "cpu"


def transcribe_audio_file(audio_path: Path) -> tuple[str, str, float, str]:
    """faster-whisper를 별도 프로세스에서 실행하여 DLL 충돌을 방지합니다."""
    global _active_backend, _last_stt_error

    device = select_stt_device()
    compute_type = (
        settings.whisper_compute_type_cuda
        if device == "cuda"
        else settings.whisper_compute_type_cpu
    )
    worker_path = Path(__file__).with_name("stt_worker.py")
    command = [
        sys.executable,
        str(worker_path),
        "--audio",
        str(audio_path),
        "--model",
        settings.whisper_model_size,
        "--device",
        device,
        "--compute-type",
        compute_type,
        "--language",
        "ko",
    ]

    logger.info("STT 작업자 실행: %s", " ".join(command))
    # 현재 프로세스의 환경변수를 복사한 후 작업자 표준 입출력을 UTF-8로 강제합니다.
    worker_environment = os.environ.copy()
    # Windows PyCharm 터미널의 기본 CP949 코드페이지와 무관하게 Python 출력 인코딩을 고정합니다.
    worker_environment["PYTHONIOENCODING"] = "utf-8"
    # Python UTF-8 모드를 활성화하여 파일명과 표준 스트림 처리도 일관되게 유지합니다.
    worker_environment["PYTHONUTF8"] = "1"

    # STT 작업자를 별도 프로세스로 실행하고 표준 출력을 UTF-8로 읽습니다.
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        timeout=settings.stt_timeout_seconds,
        cwd=str(settings.project_root),
        env=worker_environment,
    )

    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    if not stdout:
        _last_stt_error = stderr or f"STT 작업자가 종료 코드 {completed.returncode}로 종료되었습니다."
        raise RuntimeError(_last_stt_error)

    # 작업자 로그가 섞이더라도 마지막 JSON 한 줄을 사용합니다.
    last_line = stdout.splitlines()[-1]
    try:
        result = json.loads(last_line)
    except json.JSONDecodeError as error:
        _last_stt_error = f"STT 작업자 응답 분석 실패: {last_line}; stderr={stderr}"
        raise RuntimeError(_last_stt_error) from error

    if completed.returncode != 0 or not result.get("ok"):
        _last_stt_error = str(result.get("error") or stderr or "알 수 없는 STT 작업자 오류")
        raise RuntimeError(_last_stt_error)

    _active_backend = str(result.get("backend", "faster-whisper-subprocess"))
    _last_stt_error = None
    return (
        str(result.get("text", "")).strip(),
        str(result.get("language", "ko") or "ko"),
        float(result.get("language_probability", 0.0) or 0.0),
        _active_backend,
    )


def determine_audio_extension(upload_file: UploadFile) -> str:
    """원본 파일명과 MIME 타입에서 안전한 음성 확장자를 결정합니다."""
    # 원본 파일명의 확장자를 소문자로 가져옵니다.
    suffix = Path(upload_file.filename or "").suffix.lower()
    # 서버에서 허용할 확장자 집합을 정의합니다.
    allowed = {".webm", ".wav", ".mp3", ".m4a", ".ogg", ".mp4"}
    # 허용 확장자인지 확인합니다.
    if suffix in allowed:
        return suffix
    # 파일명 확장자가 없을 때 MIME 타입별 확장자를 정의합니다.
    mime_extension_map = {
        "audio/webm": ".webm",
        "video/webm": ".webm",
        "audio/ogg": ".ogg",
        "audio/mp4": ".m4a",
        "video/mp4": ".mp4",
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/mpeg": ".mp3",
    }
    # MIME 타입에서 codec 파라미터를 제외한 기본 타입을 추출합니다.
    base_content_type = (upload_file.content_type or "").split(";", 1)[0].strip().lower()
    # 매핑된 확장자가 있으면 반환하고, 없으면 브라우저 기본 형식인 webm을 반환합니다.
    return mime_extension_map.get(base_content_type, ".webm")


async def save_and_transcribe_audio(upload_file: UploadFile) -> dict[str, str]:
    """음성 파일과 STT 텍스트 파일을 저장하고 접근 URL을 반환합니다."""
    # 현재 시각과 UUID를 결합해 고유 ID를 생성합니다.
    recording_id = f"{datetime.now():%Y%m%d_%H%M%S}_{uuid4().hex[:8]}"
    # 업로드 파일의 저장 확장자를 결정합니다.
    extension = determine_audio_extension(upload_file)
    # 최종 음성 파일 경로를 생성합니다.
    audio_path = settings.audio_dir / f"{recording_id}{extension}"
    # 업로드된 음성 바이너리를 읽습니다.
    audio_bytes = await upload_file.read()
    # 지나치게 짧거나 빈 녹음 파일인지 확인합니다.
    if len(audio_bytes) < settings.minimum_audio_bytes:
        raise ValueError("녹음 데이터가 너무 짧습니다. 1초 이상 말한 뒤 다시 시도해 주세요.")
    # 음성 바이너리를 서버 파일로 저장합니다.
    audio_path.write_bytes(audio_bytes)
    # faster-whisper 우선 및 자동 대체 정책으로 음성을 변환합니다.
    transcript_text, language, probability, backend = transcribe_audio_file(audio_path)
    # 인식된 문장이 없는지 확인합니다.
    if not transcript_text:
        raise ValueError("음성을 텍스트로 변환하지 못했습니다. 더 크게 다시 말해 주세요.")
    # STT 텍스트 파일 경로를 생성합니다.
    transcript_path = settings.transcript_dir / f"{recording_id}.txt"
    # 백엔드, 감지 언어, 확률, 변환 문장을 UTF-8로 저장합니다.
    transcript_path.write_text(
        f"backend={backend}\n"
        f"detected_language={language}\n"
        f"language_probability={probability:.4f}\n"
        f"text={transcript_text}\n",
        # Windows 메모장에서 파일을 바로 열어도 한글이 정상 표시되도록 UTF-8 BOM을 사용합니다.
        encoding="utf-8-sig",
    )
    # 브라우저에서 사용할 결과 딕셔너리를 반환합니다.
    return {
        "recording_id": recording_id,
        "audio_url": f"{settings.storage_url_prefix}/audio/{audio_path.name}",
        "transcript_url": f"{settings.storage_url_prefix}/transcripts/{transcript_path.name}",
        "text": transcript_text,
        "backend": backend,
    }


def get_stt_diagnostics() -> dict[str, Any]:
    """현재 STT 환경과 최근 작업자 오류 정보를 반환합니다."""
    package_names = {
        "faster-whisper": "faster_whisper",
        "ctranslate2": "ctranslate2",
        "av": "av",
    }
    packages: dict[str, dict[str, str | bool]] = {}
    for distribution_name, display_name in package_names.items():
        try:
            packages[display_name] = {
                "installed": True,
                "version": metadata.version(distribution_name),
            }
        except metadata.PackageNotFoundError:
            packages[display_name] = {
                "installed": False,
                "error": "package not installed",
            }

    return {
        "configured_backend": "faster-whisper-subprocess",
        "active_backend": _active_backend,
        "configured_device": settings.whisper_device,
        "selected_device": select_stt_device(),
        "compute_type": settings.whisper_compute_type_cpu if select_stt_device() == "cpu" else settings.whisper_compute_type_cuda,
        "worker_isolation": True,
        "last_error": _last_stt_error,
        "python_executable": sys.executable,
        "packages": packages,
    }
