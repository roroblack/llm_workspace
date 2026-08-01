# GAN MNIST PyCharm 콘솔 프로젝트

## 1. 프로젝트 목적

이 프로젝트는 GAN(Generative Adversarial Network)의 핵심 구조를 직접 실행하여 확인하는 PyCharm 콘솔 실습 프로젝트입니다.

생성자(Generator)는 무작위 잠재 벡터로부터 가짜 MNIST 숫자 이미지를 생성하고, 판별자(Discriminator)는 입력 이미지가 실제인지 가짜인지 구분합니다. 두 모델은 서로 경쟁하는 방식으로 학습합니다.

## 2. 주요 기능

- GAN 핵심 개념 콘솔 설명
- MNIST 데이터셋 자동 다운로드
- 생성자와 판별자 교대 학습
- 에포크별 가짜 숫자 이미지 저장
- 생성자 및 판별자 손실 그래프 저장
- 최신 체크포인트 자동 저장
- 체크포인트에서 이어서 학습
- 학습된 생성자로 새 이미지 생성
- CPU 및 CUDA GPU 자동 선택
- 재현성을 위한 난수 시드 고정
- 입력 오류와 실행 예외 처리

## 3. 프로젝트 구조

```text
gan_mnist_console_project/
├── main.py
├── config.py
├── requirements.txt
├── README.md
├── .gitignore
├── data/
├── outputs/
│   ├── generated/
│   ├── checkpoints/
│   └── plots/
└── src/
    ├── __init__.py
    ├── data.py
    ├── models.py
    ├── trainer.py
    └── utils.py
```

## 4. 권장 실행 환경

- Windows 10 또는 Windows 11
- Python 3.10 또는 3.11
- PyCharm
- CPU 실행 가능
- CUDA 지원 NVIDIA GPU 사용 시 학습 속도 향상

## 5. PyCharm 실행 방법

### 5.1 프로젝트 열기

1. ZIP 파일의 압축을 해제합니다.
2. PyCharm을 실행합니다.
3. `File → Open`을 선택합니다.
4. `gan_mnist_console_project` 폴더를 선택합니다.

### 5.2 가상환경 생성

PyCharm 하단 Terminal에서 다음 명령을 실행합니다.

```bash
python -m venv .venv
```

Windows PowerShell 또는 PyCharm Terminal에서 가상환경을 활성화합니다.

```powershell
.venv\Scripts\activate
```

### 5.3 패키지 설치

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

NVIDIA GPU 환경에서는 본인 CUDA 버전에 맞는 PyTorch 설치 명령을 PyTorch 공식 설치 페이지에서 확인하는 것이 좋습니다.

### 5.4 프로그램 실행

```bash
python main.py
```

또는 PyCharm에서 `main.py`를 열고 우클릭한 후 `Run 'main'`을 선택합니다.

## 6. 메뉴 사용 방법

```text
1. GAN 핵심 개념 확인
2. 새로운 GAN 모델 학습
3. 체크포인트에서 이어서 학습
4. 학습된 생성자로 이미지 생성
5. 결과 파일 저장 경로 확인
0. 프로그램 종료
```

### 메뉴 2: 새로운 모델 학습

처음 실행할 때 사용합니다. MNIST 데이터셋이 없으면 자동으로 내려받습니다.

학습 결과는 다음 위치에 저장됩니다.

- `outputs/generated/epoch_001.png`
- `outputs/generated/epoch_002.png`
- `outputs/checkpoints/gan_latest.pt`
- `outputs/checkpoints/generator_final.pt`
- `outputs/checkpoints/discriminator_final.pt`
- `outputs/plots/training_loss.png`

CPU 환경에서는 먼저 1~3 에포크로 정상 실행 여부를 확인한 뒤 에포크 수를 늘리는 것을 권장합니다.

### 메뉴 3: 이어서 학습

`outputs/checkpoints/gan_latest.pt` 파일을 불러와 기존 학습 상태에서 추가 학습합니다.

### 메뉴 4: 이미지 생성

학습된 생성자 가중치를 읽어 새로운 무작위 잠재 벡터로 숫자 이미지를 생성합니다.

결과 파일:

```text
outputs/generated/manual_generated.png
```

## 7. GAN 학습 과정

### 판별자 학습

1. 실제 MNIST 이미지를 판별자에 입력합니다.
2. 실제 이미지의 정답 레이블을 1로 설정합니다.
3. 생성자가 만든 가짜 이미지를 판별자에 입력합니다.
4. 가짜 이미지의 정답 레이블을 0으로 설정합니다.
5. 실제 손실과 가짜 손실을 합산합니다.
6. 판별자 파라미터만 갱신합니다.

### 생성자 학습

1. 무작위 잠재 벡터를 생성합니다.
2. 생성자가 가짜 이미지를 만듭니다.
3. 가짜 이미지를 판별자에 전달합니다.
4. 생성자는 판별자가 가짜 이미지를 실제인 1로 판단하게 학습합니다.
5. 생성자 파라미터만 갱신합니다.

## 8. 결과 해석

GAN 손실값은 일반 분류 모델처럼 지속적으로 감소하지 않을 수 있습니다. 생성자와 판별자가 서로 경쟁하기 때문에 두 손실은 흔들리며 변화합니다.

확인할 핵심은 다음과 같습니다.

- 에포크가 증가하면서 숫자와 비슷한 형태가 나타나는가
- 생성 이미지가 모두 똑같아지는 모드 붕괴가 발생하는가
- 한 모델만 지나치게 강해져 상대 모델의 학습이 멈추는가
- 손실값에 NaN이 발생하지 않는가

## 9. 학습 속도가 느릴 때

`config.py`에서 다음 값을 줄일 수 있습니다.

```python
batch_size = 64
epochs = 3
sample_count = 32
```

## 10. 자주 발생하는 문제

### `No module named 'torch'`

가상환경이 활성화되었는지 확인한 후 다시 설치합니다.

```bash
pip install -r requirements.txt
```

### MNIST 다운로드 오류

방화벽 또는 인터넷 연결을 확인합니다. 한 번 정상 다운로드되면 이후에는 로컬 `data` 폴더를 사용합니다.

### CUDA 메모리 부족

`config.py`에서 `batch_size`를 128에서 64 또는 32로 줄입니다.

### 생성 이미지가 이상함

GAN은 초기 에포크에서 잡음과 유사한 이미지를 생성하는 것이 정상입니다. 에포크 수를 늘려 변화를 확인합니다.
