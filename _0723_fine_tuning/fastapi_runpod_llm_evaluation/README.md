# FastAPI + RunPod 파인튜닝 모델 성능 평가 프로젝트

이 프로젝트는 PyCharm에서 코드를 작성하고 RunPod GPU Pod에 SSH/SFTP로 동기화한 뒤,
기반 모델과 파인튜닝 모델의 응답 품질 및 추론 성능을 비교할 수 있도록 구성한 실습 프로젝트입니다.

## 1. 주요 기능

- FastAPI 기반 웹 API와 간단한 평가 화면
- 로컬 CPU에서 즉시 확인 가능한 `mock` 추론 모드
- RunPod GPU에서 실제 Hugging Face 모델을 실행하는 `transformers` 추론 모드
- Base 모델과 Fine-tuned 모델 답변 생성
- Exact Match, ROUGE-1/2/L, 선택적 BERTScore 계산
- 평균 응답 시간, 중앙값 응답 시간, 초당 생성 토큰 수 계산
- JSON 형식 준수율 계산
- 모델별 JSONL 예측 결과 및 JSON 평가 보고서 저장
- 블라인드 사람 평가용 CSV 생성
- LoRA/QLoRA Adapter 병합 스크립트
- Pytest 기반 API 테스트

## 2. 권장 환경

### 로컬 PyCharm

- Windows 11
- Python 3.11
- PyCharm
- 로컬에서는 기본값인 `INFERENCE_BACKEND=mock` 사용

### RunPod

- NVIDIA GPU Pod
- Python 3.11
- CUDA를 지원하는 PyTorch 이미지
- 프로젝트 경로: `/workspace/fastapi_runpod_llm_evaluation`

작은 실습 모델은 `Qwen/Qwen2.5-0.5B-Instruct`를 기본값으로 사용합니다.
더 큰 모델을 평가할 때는 `.env`의 모델 경로를 변경합니다.

## 3. 프로젝트 구조

```text
fastapi_runpod_llm_evaluation/
├── app/
│   ├── api/
│   │   ├── evaluation.py
│   │   ├── inference.py
│   │   └── system.py
│   ├── core/
│   │   └── config.py
│   ├── models/
│   │   └── schemas.py
│   ├── services/
│   │   ├── evaluation_service.py
│   │   ├── inference_service.py
│   │   └── report_service.py
│   ├── static/
│   │   ├── app.js
│   │   └── style.css
│   ├── templates/
│   │   └── index.html
│   └── main.py
├── data/
│   └── evaluation.jsonl
├── outputs/
├── scripts/
│   ├── create_blind_review.py
│   ├── generate_predictions.py
│   ├── merge_lora_adapter.py
│   └── run_full_evaluation.py
├── tests/
│   └── test_api.py
├── .env.example
├── .gitignore
├── requirements-local.txt
├── requirements-runpod.txt
├── run_local.py
└── run_runpod.sh
```

## 4. 로컬 PyCharm 실행

### 4.1 프로젝트 열기

1. ZIP 파일의 압축을 풉니다.
2. PyCharm에서 `Open`을 선택합니다.
3. 압축 해제한 `fastapi_runpod_llm_evaluation` 폴더를 선택합니다.

### 4.2 가상환경 생성

PyCharm Terminal에서 다음 명령을 실행합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements-local.txt
```

### 4.3 환경변수 파일 생성

```powershell
copy .env.example .env
```

로컬 테스트에서는 다음 값을 유지합니다.

```env
INFERENCE_BACKEND=mock
```

### 4.4 서버 실행

```powershell
python run_local.py
```

브라우저 접속:

- 웹 화면: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- 상태 확인: `http://127.0.0.1:8000/api/system/health`

### 4.5 테스트 실행

```powershell
pytest -q
```

## 5. PyCharm과 RunPod 연결

RunPod 공식 문서에서는 Pod에 SSH로 접속하고 파일 전송 또는 IDE 원격 연결을 사용하는 방법을 제공합니다.

### 5.1 RunPod Pod 준비

1. RunPod에서 GPU Pod를 생성합니다.
2. SSH Terminal Access를 활성화합니다.
3. 공개 SSH 키를 등록합니다.
4. TCP 포트 `8000`을 노출합니다.
5. Pod의 SSH 접속 명령과 공개 포트 주소를 확인합니다.

### 5.2 PyCharm SSH Interpreter 방식

PyCharm Professional을 사용하는 경우:

1. `File → Settings → Project → Python Interpreter`
2. `Add Interpreter → On SSH`
3. RunPod가 제공한 Host, Port, Username을 입력합니다.
4. 인증에는 SSH Private Key를 선택합니다.
5. 원격 인터프리터 경로를 선택합니다.
6. 원격 프로젝트 경로를 다음과 같이 지정합니다.

```text
/workspace/fastapi_runpod_llm_evaluation
```

로컬 경로 예시:

```text
C:\LLM_workspace\fastapi_runpod_llm_evaluation
```

`.venv` 폴더는 업로드하지 않습니다. RunPod 안에서 별도로 가상환경을 생성합니다.

### 5.3 SFTP Deployment Mapping

1. `Settings → Build, Execution, Deployment → Deployment`
2. SFTP 서버를 추가합니다.
3. Root path를 `/workspace`로 지정합니다.
4. Mappings에서 다음과 같이 연결합니다.

```text
Local path:
C:\LLM_workspace\fastapi_runpod_llm_evaluation

Deployment path:
/fastapi_runpod_llm_evaluation
```

5. `.venv`, `__pycache__`, `.git`, `outputs`는 업로드 제외 항목으로 설정합니다.
6. `Tools → Deployment → Upload to ...`로 업로드합니다.

## 6. RunPod 설치 및 실행

SSH로 RunPod에 접속한 뒤 실행합니다.

```bash
cd /workspace/fastapi_runpod_llm_evaluation

python -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements-runpod.txt

cp .env.example .env
```

`.env`를 다음과 같이 수정합니다.

```env
INFERENCE_BACKEND=transformers
BASE_MODEL_PATH=Qwen/Qwen2.5-0.5B-Instruct
FINE_TUNED_MODEL_PATH=/workspace/models/merged_model
DEVICE_MAP=auto
TORCH_DTYPE=auto
```

서버 실행:

```bash
chmod +x run_runpod.sh
./run_runpod.sh
```

또는 직접 실행:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

GPU 메모리에 모델을 한 번만 적재해야 하므로 기본적으로 worker를 1개만 사용합니다.

## 7. 실제 모델 평가 순서

### 7.1 Base 모델 예측 생성

```bash
python scripts/generate_predictions.py \
  --model-kind base \
  --input-file data/evaluation.jsonl \
  --output-file outputs/base_predictions.jsonl
```

### 7.2 Fine-tuned 모델 예측 생성

```bash
python scripts/generate_predictions.py \
  --model-kind fine_tuned \
  --input-file data/evaluation.jsonl \
  --output-file outputs/fine_tuned_predictions.jsonl
```

### 7.3 전체 비교 평가

```bash
python scripts/run_full_evaluation.py
```

생성 파일:

```text
outputs/base_predictions.jsonl
outputs/fine_tuned_predictions.jsonl
outputs/base_metrics.json
outputs/fine_tuned_metrics.json
outputs/comparison.json
```

### 7.4 블라인드 평가 파일 생성

```bash
python scripts/create_blind_review.py
```

생성 파일:

```text
outputs/human_review.csv
outputs/human_review_answer_key.json
```

## 8. LoRA Adapter 병합

vLLM과 같은 서빙 엔진에서 독립 모델로 사용하려면 LoRA Adapter를 기반 모델에 병합할 수 있습니다.

```bash
python scripts/merge_lora_adapter.py \
  --base-model Qwen/Qwen2.5-0.5B-Instruct \
  --adapter-path /workspace/models/dpo_adapter \
  --output-path /workspace/models/merged_model
```

주의:

- 4비트로 불러온 모델에 바로 병합하지 않습니다.
- 병합 시 Base 모델을 FP16 또는 BF16으로 다시 불러옵니다.
- 병합 결과가 Adapter 직접 로딩 결과와 유사한지 샘플 비교를 수행합니다.

## 9. API 사용 예시

### 상태 확인

```bash
curl http://127.0.0.1:8000/api/system/health
```

### 단일 질문 추론

```bash
curl -X POST http://127.0.0.1:8000/api/inference/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model_kind": "base",
    "prompt": "파인튜닝 모델 평가 방법을 설명하세요.",
    "max_new_tokens": 128
  }'
```

### 한 모델 평가

```bash
curl -X POST http://127.0.0.1:8000/api/evaluation/run \
  -H "Content-Type: application/json" \
  -d '{
    "model_kind": "base",
    "use_bertscore": false
  }'
```

### Base와 Fine-tuned 모델 비교

```bash
curl -X POST http://127.0.0.1:8000/api/evaluation/compare \
  -H "Content-Type: application/json" \
  -d '{
    "use_bertscore": false
  }'
```

## 10. 평가 결과 해석

- `exact_match`: 기준 답변과 정규화 후 완전히 같은 비율
- `rouge1_f1`: 단어 단위 중복 기반 F1
- `rouge2_f1`: 연속된 두 토큰 중복 기반 F1
- `rougeL_f1`: 최장 공통 부분 수열 기반 F1
- `bertscore_f1`: 문맥 임베딩 기반 의미 유사도
- `json_compliance_rate`: JSON 요구 데이터 중 올바른 JSON 응답 비율
- `average_latency_seconds`: 평균 전체 생성 시간
- `median_latency_seconds`: 응답 시간의 중앙값
- `average_tokens_per_second`: 평균 초당 생성 토큰 수

ROUGE나 BERTScore가 높더라도 사실 오류가 있을 수 있으므로 블라인드 사람 평가와 안전성 검토를 함께 수행해야 합니다.

## 11. 메모리 부족 해결

GPU 메모리 부족 시 `.env`를 다음 방향으로 조정합니다.

```env
MAX_NEW_TOKENS=128
LOAD_IN_4BIT=true
```

또는 더 작은 모델을 사용합니다.

```env
BASE_MODEL_PATH=Qwen/Qwen2.5-0.5B-Instruct
```

평가 중 Base 모델과 Fine-tuned 모델을 동시에 GPU에 적재하지 않도록 이 프로젝트는 요청 모델이 바뀌면 기존 모델을 메모리에서 해제합니다.

## 12. 참고

- FastAPI는 Uvicorn과 같은 ASGI 서버로 실행할 수 있습니다.
- Transformers의 Trainer는 학습 및 평가 루프를 제공합니다.
- PEFT의 `merge_and_unload()`는 LoRA 가중치를 기반 모델에 병합할 때 사용합니다.
- RunPod는 SSH 접속과 포트 노출 기능을 제공합니다.
