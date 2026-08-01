"""업로드 음성의 STT 변환과 서버 측 TTS 파일 생성을 담당합니다."""

# WAV 파일의 헤더와 PCM 샘플을 표준 라이브러리만으로 읽기 위해 wave를 사용합니다.
import wave

# 파일 이름 충돌을 방지하기 위한 UUID를 가져옵니다.
from uuid import uuid4

# TTS 엔진을 여러 요청이 동시에 사용하지 않도록 잠금을 사용합니다.
from threading import Lock

# 배열 연산과 샘플링 주파수 변환에 NumPy를 사용합니다.
import numpy as np

# PyTorch의 추론 모드를 사용하여 불필요한 그래디언트 메모리를 막습니다.
import torch

# 저장 경로를 가져옵니다.
from app.config import AUDIO_DIR

# Whisper 지연 로딩 관리자를 가져옵니다.
from app.services.model_manager import ModelManager


# pyttsx3 엔진은 동시에 실행하면 충돌할 수 있으므로 전역 잠금을 둡니다.
_tts_lock = Lock()


def _read_pcm_wav(audio_path: str) -> tuple[np.ndarray, int]:
    """브라우저가 전송한 PCM WAV를 -1.0~1.0 범위의 단일 채널 파형으로 읽습니다."""

    # wave.open은 외부 FFmpeg 없이 표준 PCM WAV 파일을 직접 처리합니다.
    with wave.open(audio_path, "rb") as wav_file:
        # 원본 오디오의 채널 수를 확인합니다.
        channels = wav_file.getnchannels()

        # 한 샘플이 차지하는 바이트 수를 확인합니다.
        sample_width = wav_file.getsampwidth()

        # 원본 샘플링 주파수를 확인합니다.
        sample_rate = wav_file.getframerate()

        # 전체 PCM 프레임을 바이트 배열로 읽습니다.
        raw_frames = wav_file.readframes(wav_file.getnframes())

    # 프론트엔드가 생성하는 16비트 PCM이 아닌 파일은 잘못된 입력으로 처리합니다.
    if sample_width != 2:
        raise ValueError("STT 입력 WAV는 16비트 PCM 형식이어야 합니다.")

    # 16비트 정수 PCM을 NumPy 배열로 해석합니다.
    audio = np.frombuffer(raw_frames, dtype=np.int16).astype(np.float32)

    # 스테레오 이상인 경우 채널별 평균으로 단일 채널 음성을 만듭니다.
    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1)

    # Whisper가 기대하는 -1.0~1.0 부동소수점 범위로 정규화합니다.
    audio /= 32768.0

    # 파형과 원본 샘플링 주파수를 반환합니다.
    return audio, sample_rate


def _resample_linear(audio: np.ndarray, source_rate: int, target_rate: int = 16000) -> np.ndarray:
    """외부 오디오 라이브러리 없이 선형 보간으로 16kHz 파형을 만듭니다."""

    # 이미 목표 샘플링 주파수이면 복사 없이 그대로 반환합니다.
    if source_rate == target_rate:
        return audio

    # 비정상적인 샘플링 주파수는 계산 전에 거부합니다.
    if source_rate <= 0:
        raise ValueError("올바르지 않은 WAV 샘플링 주파수입니다.")

    # 변환 후 필요한 전체 샘플 개수를 계산합니다.
    target_length = max(1, round(len(audio) * target_rate / source_rate))

    # 원본 파형 위치를 0~1의 정규화 좌표로 표현합니다.
    source_positions = np.linspace(0.0, 1.0, num=len(audio), endpoint=False)

    # 목표 파형 위치를 같은 좌표계로 생성합니다.
    target_positions = np.linspace(0.0, 1.0, num=target_length, endpoint=False)

    # 선형 보간을 수행하고 Whisper 입력에 적합한 float32로 반환합니다.
    return np.interp(target_positions, source_positions, audio).astype(np.float32)


def transcribe_audio(audio_path: str) -> dict[str, str]:
    """PyTorch 기반 Whisper로 PCM WAV 음성을 자연스러운 한국어 문장으로 변환합니다."""

    # 표준 WAV 리더로 음성 파형과 샘플링 주파수를 읽습니다.
    audio, sample_rate = _read_pcm_wav(audio_path)

    # 지나치게 짧거나 사실상 무음인 입력을 모델 실행 전에 검출합니다.
    if audio.size < sample_rate // 2 or float(np.max(np.abs(audio), initial=0.0)) < 0.001:
        raise ValueError("음성이 감지되지 않았습니다. 1초 이상 또렷하게 말해 주세요.")

    # Whisper 표준 입력 주파수인 16kHz 단일 채널 파형으로 변환합니다.
    audio_16k = _resample_linear(audio, sample_rate, 16000)

    # CTranslate2 DLL이 필요 없는 Hugging Face 프로세서와 PyTorch 모델을 준비합니다.
    processor, model = ModelManager.get_whisper_components()

    # 실수 파형을 Whisper의 log-Mel 입력 특징과 attention mask로 변환합니다.
    model_inputs = processor(
        audio_16k,
        sampling_rate=16000,
        return_tensors="pt",
        return_attention_mask=True,
    )

    # 입력 특징을 모델과 같은 CPU 또는 GPU 장치로 이동합니다.
    input_features = model_inputs.input_features.to(ModelManager.torch_device())

    # attention mask가 제공된 경우 같은 장치로 이동합니다.
    attention_mask = getattr(model_inputs, "attention_mask", None)
    if attention_mask is not None:
        attention_mask = attention_mask.to(ModelManager.torch_device())

    # 그래디언트를 만들지 않는 추론 모드에서 한국어 받아쓰기를 수행합니다.
    with torch.inference_mode():
        generated_ids = model.generate(
            input_features=input_features,
            attention_mask=attention_mask,
            language="ko",
            task="transcribe",
            max_new_tokens=256,
        )

    # 생성된 토큰 ID에서 특수 토큰을 제거하고 사람이 읽는 문장으로 복원합니다.
    text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()

    # 모델 결과가 비어 있으면 녹음 상태를 확인할 수 있는 메시지를 반환합니다.
    if not text:
        raise ValueError("음성이 감지되지 않았습니다. 마이크와 녹음 음량을 확인하세요.")

    # 인식 문장과 고정된 대상 언어 정보를 반환합니다.
    return {"text": text, "language": "ko"}


def synthesize_speech(text: str) -> dict[str, str]:
    """pyttsx3를 사용하여 텍스트를 WAV 음성 파일로 저장합니다."""

    # 비어 있는 텍스트에 대해서는 음성 파일을 만들지 않습니다.
    if not text.strip():
        raise ValueError("음성으로 변환할 텍스트를 입력해야 합니다.")

    # pyttsx3는 운영체제의 음성 합성 엔진을 이용하므로 실행 시점에 가져옵니다.
    import pyttsx3

    # UUID 기반 WAV 파일 이름을 생성합니다.
    filename = f"tts_{uuid4().hex}.wav"

    # 음성 파일의 절대 저장 경로를 구성합니다.
    output_path = AUDIO_DIR / filename

    # 하나의 pyttsx3 엔진만 실행되도록 잠금 범위에서 처리합니다.
    with _tts_lock:
        # Windows에서는 SAPI5, macOS에서는 NSSpeechSynthesizer, Linux에서는 eSpeak를 자동 사용합니다.
        engine = pyttsx3.init()

        # 지나치게 빠르지 않은 분당 발화 속도로 설정합니다.
        engine.setProperty("rate", 170)

        # 시스템에 설치된 음성 중 한국어로 추정되는 음성을 찾아 적용합니다.
        for voice in engine.getProperty("voices"):
            voice_description = f"{voice.id} {voice.name}".lower()
            if "korean" in voice_description or "ko-kr" in voice_description or "heami" in voice_description:
                engine.setProperty("voice", voice.id)
                break

        # 입력 문장을 WAV 파일로 저장하도록 작업 큐에 등록합니다.
        engine.save_to_file(text.strip(), str(output_path))

        # 등록한 합성 작업이 끝날 때까지 실행합니다.
        engine.runAndWait()

        # 네이티브 음성 엔진 리소스를 해제합니다.
        engine.stop()

    # 일부 Linux 환경에서 TTS 엔진이 실패해 파일이 생성되지 않은 경우 오류를 알립니다.
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError("서버 TTS 파일을 생성하지 못했습니다. 운영체제 음성 엔진을 확인하세요.")

    # 브라우저가 재생할 수 있는 음성 파일 URL을 반환합니다.
    return {"audio_url": f"/media/audio/{filename}"}
