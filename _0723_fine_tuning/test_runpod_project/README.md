# Qwen2.5 한국어 고객 상담 SFT 프로젝트

이 프로젝트는 `Qwen/Qwen2.5-0.5B-Instruct` 모델을 한국어 고객 상담 데이터로
Supervised Fine-Tuning하는 전체 실습 예제입니다.

학습 방식은 다음과 같습니다.

```text
사전 학습 모델
→ 4bit NF4 양자화
→ k-bit 학습 준비
→ LoRA Adapter 적용
→ SFTTrainer 학습
→ 검증
→ Adapter 저장
→ Adapter 재로드
→ 대화형 추론
```

## 1. 프로젝트 구조

```text
qwen_sft_project/
├── data/
│   ├── train.jsonl
│   └── valid.jsonl
├── outputs/
│   ├── checkpoints/
│   └── qwen2.5-korean-sft-lora/
├── 01_create_dataset.py
├── 02_train_sft.py
├── 03_inference.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

`train.jsonl`과 `valid.jsonl`은 `01_create_dataset.py` 실행 후 생성됩니다.

## 2. 권장 실행 환경

- Linux 또는 RunPod
- Python 3.10 또는 3.11
- NVIDIA CUDA GPU
- GPU VRAM 8GB 이상 권장
- CUDA가 지원되는 PyTorch
- 인터넷 연결

Windows 로컬 환경에서는 `bitsandbytes`와 CUDA 조합에서 문제가 생길 수 있으므로
RunPod, Ubuntu 또는 WSL2 환경을 권장합니다.

## 3. 가상환경 생성 (runpod 에는 가상환경 생성이 필요없음)

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Linux 또는 RunPod

```bash
python -m venv .venv
source .venv/bin/activate
```

## 4. 라이브러리 설치 (runpod ssh 터미널에서 직접 명령어 실행함)

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

PyTorch가 GPU를 인식하는지 확인합니다.

```bash
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CUDA 없음')"
```

## 5. 환경변수 설정

`.env.example`을 복사하여 `.env` 파일을 만듭니다.

### Windows

```powershell
Copy-Item .env.example .env
```

### Linux

```bash
cp .env.example .env
```

공개 모델만 사용할 경우 `HF_TOKEN`은 비워 두어도 됩니다.

```dotenv
HF_TOKEN=
MODEL_NAME=Qwen/Qwen2.5-0.5B-Instruct
OUTPUT_DIR=outputs/qwen2.5-korean-sft-lora
```

### Hugging Face 토큰 받기

1단계. Hugging Face 회원가입

브라우저에서 다음 사이트에 접속합니다.
https://huggingface.co

우측 상단의 Sign Up을 클릭합니다.

가입 방법

이메일 가입
GitHub 계정
Google 계정

가입을 완료한 후 로그인합니다.

2단계. 프로필 메뉴 열기

로그인 후 우측 상단의 프로필 아이콘을 클릭합니다.

다음 메뉴를 선택합니다.
Settings
3단계. Access Tokens 메뉴 선택

왼쪽 메뉴에서
Access Tokens
를 클릭합니다.

직접 이동하려면 다음 페이지를 열어도 됩니다.
https://huggingface.co/settings/tokens

4단계. 새 토큰 생성

다음을 클릭합니다.
Create new token

또는
New token
(화면 버전에 따라 이름이 조금 다를 수 있습니다.)

5단계. 토큰 정보 입력

예를 들어

Token name
runpod

권한(Role)은 일반적으로 다음을 선택하면 됩니다.
Read

권한 설명

Read: 모델 다운로드(권장)
Write: 업로드 가능
Fine-grained: 세부 권한 설정

대부분의 실습에서는 Read 권한만으로 충분합니다.

6단계. Create 클릭

생성이 완료되면 다음과 같은 형태의 토큰이 한 번만 표시됩니다.
hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

예)
hf_A1B2C3D4E5F6G7H8I9J0K...

이 토큰은 한 번만 표시되므로 안전한 곳에 복사해 두십시오.

## 6. 데이터셋 생성

```bash
python 01_create_dataset.py
```

정상 결과 예시:

```text
전체 데이터 수 : 20
학습 데이터 수 : 16
검증 데이터 수 : 4
```

## 7. 모델 학습

```bash
python 02_train_sft.py
```

학습 과정에서 다음 정보가 출력됩니다.

- PyTorch와 CUDA 정보
- GPU 이름과 VRAM
- 학습 및 검증 데이터 수
- 전체 파라미터 수
- LoRA 학습 가능 파라미터 수
- Training Loss
- Evaluation Loss
- Adapter 저장 경로
- 간단한 추론 결과

## 8. 저장 결과

정상 학습 후 다음과 같은 파일이 생성됩니다.

```text
outputs/qwen2.5-korean-sft-lora/
├── adapter_config.json
├── adapter_model.safetensors
├── tokenizer.json
├── tokenizer_config.json
├── special_tokens_map.json
├── training_summary.json
└── test_generation.json
```

`adapter_model.safetensors`는 전체 기본 모델이 아니라 학습된 LoRA Adapter입니다.

## 9. 대화형 추론

```bash
python 03_inference.py
```

실행 예시:

```text
질문: 배송 완료라고 나오는데 상품을 받지 못했습니다.

답변: 먼저 가족, 경비실, 무인 택배함 또는 문 앞에 상품이 보관되었는지
확인해 주세요. 확인되지 않으면 택배사에 문의한 뒤 주문번호와 함께
고객센터로 문의해 주세요.
```

## 10. TensorBoard

```bash
tensorboard --logdir outputs/checkpoints/runs
```

RunPod에서는 다음과 같이 실행합니다.

```bash
tensorboard \
  --logdir outputs/checkpoints/runs \
  --host 0.0.0.0 \
  --port 6006
```

RunPod Pod 설정에서 HTTP Port `6006`을 연결한 뒤 접속합니다.

## 11. CUDA 메모리 부족 해결

`CUDA out of memory`가 발생하면 `02_train_sft.py`에서 다음 값을 조정합니다.

```python
MAX_LENGTH = 256
TRAIN_BATCH_SIZE = 1
GRADIENT_ACCUMULATION_STEPS = 16
```

LoRA Rank도 줄일 수 있습니다.

```python
r=8
```

LoRA 적용 대상을 Attention Projection으로만 제한할 수도 있습니다.

```python
target_modules=[
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",
]
```

## 12. TRL 버전 호환성 참고

TRL 버전에 따라 `SFTConfig`의 일부 인자 이름이 변경될 수 있습니다.

현재 코드에서 다음 오류가 발생할 경우:

```text
TypeError: SFTConfig.__init__() got an unexpected keyword argument 'eval_strategy'
```

설치된 TRL 및 Transformers를 최신 버전으로 업데이트합니다.

```bash
pip install -U transformers datasets trl peft accelerate bitsandbytes
```

반대로 구버전 사용이 필요한 환경에서는 다음과 같이 변경해야 할 수 있습니다.

```python
evaluation_strategy="epoch"
```

## 13. 실습 성공 기준

1. CUDA GPU가 인식됩니다.
2. 기본 모델과 Tokenizer가 다운로드됩니다.
3. 학습/검증 JSONL 파일이 생성됩니다.
4. LoRA 학습 가능 파라미터가 출력됩니다.
5. Training Loss가 출력됩니다.
6. Evaluation Loss가 출력됩니다.
7. `adapter_model.safetensors`가 저장됩니다.
8. 저장된 Adapter가 다시 로드됩니다.
9. 사용자 질문에 대해 한국어 답변이 생성됩니다.

첫 실습에서는 답변 품질보다 전체 파이프라인이 중단 없이 실행되는지를 우선 확인합니다.
