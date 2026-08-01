$ErrorActionPreference = "Stop"

Write-Host "[1/6] 기존 가상환경을 삭제합니다."
if (Test-Path ".venv") {
    Remove-Item -Recurse -Force ".venv"
}

Write-Host "[2/6] Python 3.11 가상환경을 생성합니다."
py -3.11 -m venv .venv

Write-Host "[3/6] 가상환경을 활성화합니다."
& .\.venv\Scripts\Activate.ps1

Write-Host "[4/6] 설치 도구를 갱신합니다."
python -m pip install --upgrade pip setuptools wheel

Write-Host "[5/6] 프로젝트 패키지를 설치합니다."
python -m pip install --no-cache-dir -r requirements.txt

Write-Host "[6/6] STT 핵심 모듈을 검사합니다."
python -c "from faster_whisper import WhisperModel; import ctranslate2, av; print('faster-whisper import: OK'); print('ctranslate2:', ctranslate2.__version__); print('av:', av.__version__)"

Write-Host "서버를 시작합니다."
python run.py
