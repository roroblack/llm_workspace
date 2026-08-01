# HuggingFace Transformers 추론 서비스 (FastAPI)

HuggingFace `pipeline`(전처리 → 추론 → 후처리)을 FastAPI 로 감싼 REST 서비스.
감성분석 / 요약 / 번역 3개 태스크를 제공한다.

## 환경

Windows + CPU + Python 3.11

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
```

> `--extra-index-url`이 없으면 CUDA 빌드 torch(약 2.5GB)를 받으려 해서
> CPU 환경에서 불필요하게 무겁다.

## 실행

```powershell
uvicorn app.main:app --reload
```

- Swagger UI: http://127.0.0.1:8000/docs
- 헬스체크: http://127.0.0.1:8000/health (모델 로딩 여부·로딩 소요시간 확인)

## 구조

```
testHuggingFace/
  app/
    main.py                  # FastAPI 앱, lifespan, /health
    core/
      config.py              # 설정(모델명/캐시/한계값) — 환경변수로 override
      hf/pipelines.py        # pipeline 싱글톤 레지스트리 + 토큰 기준 분할 유틸
    models/schemas.py        # 요청/응답 Pydantic 스키마 (+ Swagger 예시)
    routers/nlp_router.py    # /nlp/classify, /nlp/summarize, /nlp/translate
  scripts/verify_endpoints.py  # 개요 문서의 테스트 케이스 일괄 검증
  requirements.txt
  .env.example
```

## 엔드포인트

| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | `/nlp/classify` | 감성분석. `text`(단건) 또는 `texts`(배치). `top_k`로 라벨 분포 확인 |
| POST | `/nlp/summarize` | 추상적 요약. 입력이 모델 한계를 넘으면 map-reduce 로 자동 분할 |
| POST | `/nlp/translate` | 번역(기본 영→한). NLLB 사용 시 `src_lang`/`tgt_lang` 지정 가능 |
| GET | `/health` | 앱 상태 + 태스크별 모델 로딩 여부/로딩 시간 |

## 기본 모델

| 태스크 | 모델 | 크기 |
|---|---|---|
| 감성분석 | `distilbert-base-uncased-finetuned-sst-2-english` | ~260MB |
| 요약 | `sshleifer/distilbart-cnn-6-6` | ~800MB |
| 번역 | `facebook/nllb-200-distilled-600M` | ~2.4GB |

`.env` 로 전부 교체 가능하다 (`.env.example` 참고).

### 요약 모델을 `facebook/bart-large-cnn` 으로 쓰려면

`bart-large-cnn` 은 요약 품질이 더 좋은 원본 모델이고, `distilbart-cnn-6-6` 은 그 증류판이다.
이 프로젝트는 **CPU + 저메모리 환경**을 고려해 증류판을 기본값으로 뒀다.

```dotenv
SUMMARIZATION_MODEL=facebook/bart-large-cnn
```

한 줄로 교체되며 코드 수정은 필요 없다. 다만 자원 비용을 감안할 것:

| | distilbart-cnn-6-6 (기본) | bart-large-cnn |
|---|---|---|
| 다운로드 | ~800MB | ~1.6GB |
| 디스크 실사용 | ~1.6GB | ~3.2GB (Windows 심링크 미지원 시 2배) |
| 메모리(fp32) | ~0.8GB | ~1.6GB |
| 요약 품질 | 양호 | 더 좋음 |

## 구현상 알아둘 점

- **모델 싱글톤**: `pipeline()` 은 다운로드 + 가중치 로딩이라 요청마다 만들면 안 된다.
  `PipelineRegistry` 가 태스크별로 1개만 만들어 재사용하며, 태스크별 락 +
  double-checked locking 으로 동시 요청 시 중복 로딩을 막는다.
- **선택 프리로드**: `PRELOAD_MODELS` 에 태스크를 골라 지정한다.
  빈 값이면 전부 lazy(첫 요청 때 로딩), `all` 이면 3종 전부,
  `classification,summarization` 처럼 쓰면 지정한 것만 기동 시 올린다.
  자주 쓰는 태스크만 올려 첫 요청 지연을 없애면서 메모리는 아끼는 것이 목적이다.

  > 3종 전부(`all`)는 fp32 가중치 합계가 약 3.5GB다. 가용 메모리 3.6GB 환경에서
  > `OpenBLAS error: Memory allocation still failed` 로 기동이 죽는 것을 확인했다.
  > 메모리가 빠듯하면 반드시 골라서 지정할 것.
- **캐시 폴더**: 모델은 `~/.cache/huggingface` 에 저장된다. 최초 1회만 다운로드하고
  이후엔 캐시에서 로딩한다. `HF_HOME` 으로 위치 변경 가능.
- **blocking 추론**: 추론은 CPU 바운드다. 라우터 핸들러를 `async def` 가 아니라
  `def` 로 선언해 FastAPI 가 threadpool 로 넘기게 했다. `async def` 였다면
  추론 중 이벤트 루프가 통째로 멈춘다.
- **요약 입력 한계**: BART 계열은 입력 약 1024 토큰이 상한이고, 넘으면 **조용히 잘린다**.
  그대로 두면 긴 문서의 뒷부분이 요약에서 통째로 빠지므로, 문장 경계 기준으로
  청크를 나눠 각각 요약하고(map) 그 결과를 다시 요약한다(reduce).
  응답의 `strategy`/`chunks` 필드로 어느 경로를 탔는지 확인할 수 있다.
- **감성분석 라벨**: SST-2 모델은 POSITIVE/NEGATIVE 2진 분류라 **중립 라벨이 없다.**
  중립 문장도 둘 중 하나로 강제 분류되므로, `top_k=2` 로 두 확률을 함께 보고
  0.5~0.7 대면 경계 케이스로 해석해야 한다.

## 검증

```powershell
# 터미널 1
uvicorn app.main:app
# 터미널 2
python scripts/verify_endpoints.py --out reports/verification.json
```

개요 문서에 적힌 테스트 케이스(감성 4종 + 배치, 요약 2종, 번역 4종)를 전부 호출하고
결과를 JSON 으로 남긴다.
