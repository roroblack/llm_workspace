# Qwen2.5 한국어 고객 상담 SFT (QLoRA) 실습

PEFT 파인튜닝 교재 3장 "Supervised Fine-tuning 실습"을 코드로 구현한 프로젝트입니다.
`Qwen/Qwen2.5-0.5B-Instruct` 모델을 한국어 고객 상담 데이터로 **QLoRA(4bit + LoRA)** 방식으로 SFT합니다.

## 전체 파이프라인

```
GPU 확인 → 라이브러리 설치 → 학습 데이터 생성/검증 → Tokenizer 로드
→ 사전 학습 모델 4bit 로드 → LoRA Adapter 설정 → SFTTrainer 구성
→ 모델 학습 → Adapter 저장 → 학습 전·후 추론 비교 → 저장된 Adapter 재로드
```

## 프로젝트 구조

```
test_runpod_project/
├── data/                       # 01번 스크립트가 생성 (train.jsonl, valid.jsonl)
├── outputs/
│   ├── checkpoints/            # Trainer 체크포인트 및 TensorBoard 로그
│   └── qwen2.5-korean-sft-lora/  # 최종 LoRA Adapter
├── 01_create_dataset.py        # SFT 학습 데이터 생성
├── 02_train_sft.py             # QLoRA SFT 학습 전체 코드
├── 03_inference.py             # 저장된 Adapter 재로드 후 대화형 추론
├── main.py                     # GPU/CUDA 환경 확인용
├── requirements.txt
├── .env.example
└── README.md
```

> QLoRA(4bit) 학습에는 NVIDIA GPU가 필요합니다. RunPod GPU Pod 또는 Google Colab 환경에서 실행하세요.
> `bitsandbytes`는 CPU 전용 환경에서는 동작하지 않으므로, `02_train_sft.py`/`03_inference.py`는 GPU 환경에서 실행해야 합니다.
> `01_create_dataset.py`는 순수 파이썬이므로 GPU 없이도 실행됩니다.

## 실행 순서

### 1. 가상환경 생성

```bash
# Windows PowerShell / PyCharm Terminal
python -m venv .venv
.venv\Scripts\activate

# RunPod / Linux
python -m venv .venv
source .venv/bin/activate
```

### 2. 라이브러리 설치

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 3. 환경변수 설정

`.env.example`을 `.env`로 복사합니다. 공개 모델만 사용한다면 `HF_TOKEN`은 비워 두어도 됩니다.

```
HF_TOKEN=
MODEL_NAME=Qwen/Qwen2.5-0.5B-Instruct
OUTPUT_DIR=outputs/qwen2.5-korean-sft-lora
```

### 4. 학습 데이터 생성

```bash
python 01_create_dataset.py
```

전체 20개 샘플을 8:2로 나누어 `data/train.jsonl`(16개), `data/valid.jsonl`(4개)을 생성합니다.

### 5. 모델 학습

```bash
python 02_train_sft.py
```

학습 완료 후 `outputs/qwen2.5-korean-sft-lora/`에 다음 파일이 생성됩니다.

```
adapter_config.json
adapter_model.safetensors   # 전체 모델이 아닌 학습된 LoRA 파라미터만 저장
tokenizer.json / tokenizer_config.json / special_tokens_map.json
training_summary.json
test_generation.json
```

### 6. 저장된 모델 추론

```bash
python 03_inference.py
```

`질문:` 프롬프트에 상담 질문을 입력하면 답변이 생성됩니다. `종료`, `exit`, `quit`으로 종료합니다.

## TensorBoard로 학습 Loss 확인

```bash
tensorboard --logdir outputs/checkpoints/runs
# RunPod 외부 접속
tensorboard --logdir outputs/checkpoints/runs --host 0.0.0.0 --port 6006
```

## GPU 메모리 부족(CUDA out of memory) 시 조정 순서

`02_train_sft.py`에서 다음 순서로 값을 낮춥니다.

- `MAX_LENGTH = 256` (512 → 256)
- `TRAIN_BATCH_SIZE = 1` 유지
- `GRADIENT_ACCUMULATION_STEPS = 16` (유효 배치 크기 확보)
- LoRA `r = 8` (16 → 8)
- `target_modules`를 Attention 계열(`q_proj`, `k_proj`, `v_proj`, `o_proj`)로 축소

## 실습 성공 확인 기준

1. CUDA GPU가 정상적으로 인식된다.
2. Qwen 기본 모델과 Tokenizer가 다운로드된다.
3. `train.jsonl`과 `valid.jsonl`이 로드된다.
4. LoRA 학습 가능 파라미터 수가 출력된다.
5. 학습 과정에서 Loss가 출력된다.
6. 검증 데이터의 `eval_loss`가 출력된다.
7. `adapter_model.safetensors`가 저장된다.
8. 저장된 Adapter를 다시 불러올 수 있다.
9. 사용자 질문에 대해 답변이 생성된다.
10. `training_summary.json`과 `test_generation.json`이 저장된다.

이 실습의 1차 성공 기준은 답변 품질 자체보다
**데이터 준비 → 모델 로드 → SFT 학습 → Adapter 저장 → 재로드 → 추론**까지의
전체 과정이 중단 없이 실행되는 것입니다.
