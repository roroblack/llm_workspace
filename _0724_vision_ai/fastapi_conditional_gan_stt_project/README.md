# FastAPI + Conditional GAN + Microphone STT

Python 3.11 및 PyCharm용 FastAPI 실습 프로젝트입니다.

## 구현 기능

- Google 검색창 형태의 프롬프트 입력 UI
- 마이크 아이콘과 녹음 상태 표시
- 브라우저 MediaRecorder 기반 녹음
- 녹음 파일 서버 저장
- faster-whisper 기반 한국어 STT
- STT 텍스트 파일 저장
- STT 결과를 프롬프트 입력창에 자동 반영
- 프롬프트에서 숫자 0~9 조건 추출
- MNIST 조건부 GAN 학습
- 실제 학습 에포크별 생성 이미지 저장
- 프론트에서 진행률, 손실값, 에포크 이미지 표시
- 최종 이미지와 원본 프롬프트 동시 표시
- 생성자 및 판별자 모델 저장

## 중요한 범위

이 프로젝트는 MNIST 조건부 GAN 실습입니다. 따라서 프롬프트에는 숫자 0~9 또는 한글/영어 숫자 단어가 포함되어야 합니다.

예시:

```text
숫자 7을 생성해 주세요
손글씨 칠 이미지
Generate number three
```

강아지, 풍경, 인물과 같은 범용 이미지를 생성하는 Stable Diffusion 프로젝트는 아닙니다.

## 프로젝트 구조

```text
fastapi_conditional_gan_stt_project/
├── app/
│   ├── main.py
│   ├── api/routes.py
│   ├── core/config.py
│   ├── models/conditional_gan.py
│   ├── schemas/generation.py
│   ├── services/
│   │   ├── gan_service.py
│   │   ├── job_manager.py
│   │   ├── prompt_service.py
│   │   └── stt_service.py
│   ├── static/css/style.css
│   ├── static/js/app.js
│   └── templates/index.html
├── data/
├── storage/
├── run.py
├── requirements.txt
└── README.md
```

## PyCharm 실행

```powershell
py -3.11 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
python run.py
```

브라우저 접속:

```text
http://127.0.0.1:8000
```

## 사용 순서

1. 마이크 아이콘을 누릅니다.
2. 브라우저에서 마이크 권한을 허용합니다.
3. “숫자 칠을 생성해 주세요”라고 말합니다.
4. 마이크 아이콘을 다시 눌러 녹음을 종료합니다.
5. 녹음 파일과 STT 텍스트가 서버에 저장됩니다.
6. 변환 텍스트가 프롬프트 입력창에 자동으로 표시됩니다.
7. 학습 에포크를 입력합니다.
8. 생성 버튼을 누릅니다.
9. 에포크마다 이미지가 저장되고 화면에 순서대로 표시됩니다.
10. 마지막 이미지와 프롬프트가 최종 결과 영역에 표시됩니다.

## 저장 경로

```text
storage/audio/{recording_id}.webm
storage/transcripts/{recording_id}.txt
storage/generations/{job_id}/prompt.txt
storage/generations/{job_id}/epoch_001.png
storage/generations/{job_id}/epoch_002.png
storage/models/{job_id}_generator.pt
storage/models/{job_id}_discriminator.pt
```

## 실행 속도 조절

CPU에서 먼저 다음과 같이 실행하는 것이 좋습니다.

- 에포크: 1
- 학습 샘플: 3,000~10,000

PowerShell 예시:

```powershell
$env:GAN_MAX_TRAINING_SAMPLES="3000"
$env:WHISPER_MODEL_SIZE="base"
python run.py
```

첫 STT 실행 시 Whisper 모델을 다운로드하므로 시간이 더 필요합니다.

## 주의 사항

- 마이크 기능은 `127.0.0.1` 또는 `localhost` 접속에서 사용하는 것이 안전합니다.
- 서버를 재시작하면 메모리 기반 작업 상태는 초기화됩니다.
- 생성 이미지, 녹음 파일, STT 텍스트, 모델 파일은 디스크에 유지됩니다.
- 여러 GAN 작업을 동시에 요청하면 CPU/GPU 메모리 사용량이 증가할 수 있습니다.


### STT 진단 주소

서버 실행 후 브라우저에서 다음 주소를 확인합니다.

```text
http://127.0.0.1:8000/api/stt/diagnostics
```

정상적인 Windows 기본 결과 예시는 다음과 같습니다.

```json
{
  "configured_backend": "auto",
  "windows_auto_policy": "openai-whisper",
  "selected_faster_whisper_device": "cpu",
  "torch_cuda_available": true
}
```

`torch_cuda_available`이 `true`여도 `selected_faster_whisper_device`가 `cpu`인 것은
CTranslate2 CUDA DLL 충돌을 방지하기 위한 정상 동작입니다.

### 백엔드 수동 선택

PowerShell에서 다음 중 하나를 선택할 수 있습니다.

```powershell
# 권장: faster-whisper 우선, 실패 시 openai-whisper 자동 대체
$env:STT_BACKEND="auto"

# CTranslate2 DLL 문제가 계속되면 openai-whisper만 사용
$env:STT_BACKEND="openai-whisper"

# faster-whisper 오류를 그대로 확인하려는 경우
$env:STT_BACKEND="faster-whisper"
```
