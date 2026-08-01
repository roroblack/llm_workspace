"""faster-whisper를 FastAPI 프로세스와 분리하여 실행하는 STT 작업자입니다."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def configure_standard_streams() -> None:
    """Windows 콘솔 코드페이지와 관계없이 표준 입출력을 UTF-8로 고정합니다."""
    # Python 3.7 이상에서는 TextIOWrapper의 인코딩을 실행 중에 재설정할 수 있습니다.
    # PyCharm 터미널이 CP949로 실행되더라도 작업자 출력이 UTF-8로 유지되도록 합니다.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="strict")
    # 오류 메시지에도 한글이 포함될 수 있으므로 stderr 역시 UTF-8로 고정합니다.
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def emit_json(payload: dict[str, Any]) -> None:
    """프로세스 간 전달용 JSON을 ASCII 문자만 사용하여 안전하게 출력합니다."""
    # ensure_ascii=True는 한글을 \uXXXX 형식으로 출력합니다.
    # JSON을 읽는 부모 프로세스에서는 원래 한글 문자열로 자동 복원되므로,
    # Windows CP949/UTF-8 코드페이지 차이로 인한 깨짐을 근본적으로 차단합니다.
    print(json.dumps(payload, ensure_ascii=True), flush=True)


def main() -> int:
    """명령행 인수를 받아 음성을 변환한 후 JSON 한 줄을 반환합니다."""
    # 작업자 프로세스가 시작되자마자 표준 스트림 인코딩을 UTF-8로 고정합니다.
    configure_standard_streams()

    # STT 작업자 실행에 필요한 명령행 인수 파서를 생성합니다.
    parser = argparse.ArgumentParser()
    # 변환할 음성 파일 경로를 필수 인수로 받습니다.
    parser.add_argument("--audio", required=True)
    # 사용할 Whisper 모델 크기를 받습니다.
    parser.add_argument("--model", default="base")
    # STT 실행 장치를 CPU 또는 CUDA로 받습니다.
    parser.add_argument("--device", default="cpu")
    # CTranslate2 계산 형식을 받습니다.
    parser.add_argument("--compute-type", default="int8")
    # 음성 인식 언어를 받으며 한국어를 기본값으로 사용합니다.
    parser.add_argument("--language", default="ko")
    # 전달된 명령행 인수를 분석합니다.
    args = parser.parse_args()

    # 문자열로 전달된 음성 파일 경로를 Path 객체로 변환합니다.
    audio_path = Path(args.audio)
    # 음성 파일이 실제로 존재하는지 검사합니다.
    if not audio_path.exists():
        # 오류 결과도 ASCII 전용 JSON으로 출력하여 한글 경로가 깨지지 않게 합니다.
        emit_json({"ok": False, "error": f"음성 파일을 찾을 수 없습니다: {audio_path}"})
        return 2

    try:
        # 이 작업자 프로세스에서는 torch를 가져오지 않습니다.
        # 따라서 GAN이 사용하는 PyTorch DLL과 CTranslate2 DLL의 충돌을 피할 수 있습니다.
        from faster_whisper import WhisperModel

        # 설정된 모델, 장치, 계산 형식으로 Whisper 모델을 생성합니다.
        model = WhisperModel(
            args.model,
            device=args.device,
            compute_type=args.compute_type,
        )
        # VAD와 빔 탐색을 적용하여 음성을 한국어 텍스트로 변환합니다.
        segments, info = model.transcribe(
            str(audio_path),
            language=args.language,
            vad_filter=True,
            beam_size=5,
        )
        # 여러 음성 구간의 텍스트를 공백으로 연결하여 최종 문장을 만듭니다.
        text = " ".join(
            segment.text.strip()
            for segment in segments
            if segment.text.strip()
        ).strip()
        # 부모 FastAPI 프로세스로 전달할 결과 데이터를 구성합니다.
        result = {
            "ok": True,
            "text": text,
            "language": str(getattr(info, "language", args.language) or args.language),
            "language_probability": float(
                getattr(info, "language_probability", 0.0) or 0.0
            ),
            "backend": "faster-whisper-subprocess",
        }
        # 한글을 ASCII 이스케이프한 JSON으로 출력하여 코드페이지 문제를 방지합니다.
        emit_json(result)
        return 0
    except Exception as error:
        # 예외 이름과 메시지를 부모 프로세스가 처리할 수 있는 JSON으로 반환합니다.
        emit_json(
            {
                "ok": False,
                "error": f"{type(error).__name__}: {error}",
            }
        )
        return 1


if __name__ == "__main__":
    # 작업자 종료 코드를 운영체제에 전달합니다.
    sys.exit(main())
